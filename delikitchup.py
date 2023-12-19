import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from collections import deque
import time, json, os, shutil
import streamlit as st
import numpy as np
import copy
import input_form_function as iff
import global_value as g
import datetime
from zoneinfo import ZoneInfo
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


### 最終版の起動 #######################################################################################################

# hatomatoのstreamlitスレを見てディレクトリまで移動して起動
# モジュール化はどうしようかな

## 準備 ###########################################

# 一つのページ情報をまとめて格納
class Page:
    def __init__(self,url,id,dirChild,farChild,expState,response_message):
        #データを辞書型に格納し、json出力を容易にする
        self.data = {
            "url": url,
            "id": id,
            "dirChild": dirChild,
            "farChild": farChild,
            "expState": expState,
            "response_message": response_message
        }
    def __repr__(self):
        return str(self.data) + "\n"


linktable = [] #ID→URLを結びつけるテーブル
idtable = {} #URL→IDを結びつける辞書型
url_found = set() #set型, str格納　「既に発見済みのページか」の判定にのみ使用する。発見済みの場合、idtableにてそのIDを確認できる（負荷無し）

all_page = {} #辞書型, Page格納　キーにはページIDが入る　json出力用にページの詳細データを格納
id_not_explored = deque() #通称アクセスキュー, int格納　「次にアクセスする未探索ページID」を決定するのに使用
parents = {} #ページごとの親を格納する辞書型, int格納　「現在のページの親ページID」を決定するのに使用

blacklist = [] # アクセスしないページのURLを格納するリスト
if "blacklist" in st.session_state: # セッションステートにblacklistがあれば、それをblacklistとする
    blacklist = st.session_state["blacklist"]

#↑いくつか統合してより少ないlistで管理することも可能だが、保存されるページ数が未知数であることを考え敢えてsetで別々に管理する。
#pythonは遅いので、メモリ使用量を犠牲に実行速度を上げる工夫のつもり

#url_foundに入っているURLは必ずlinktableでIDが割り当てられており、入っていなかった場合ID割り当てと同時にアクセスキューに入る。
#そのため、他のタイミングでまたキューに入れる必要がなく、各ページのアクセスを１回に留めることができる。


def reset():
    st.session_state["all_page"] = {}
    st.session_state["linktable"] = []
    st.session_state["idtable"] = {}
    st.session_state["parents"] = {}
    g.all_page = {}
    print("reset done!")


## streamlit.sessionstate ####################
def handover():
    global all_page, idtable, linktable, parents
    
    if "all_page" in st.session_state:
        all_page = st.session_state["all_page"]
        idtable = st.session_state["idtable"]
        linktable = st.session_state["linktable"]
        parents = st.session_state["parents"]
    else:
        st.session_state["all_page"] = all_page
        st.session_state["idtable"] = idtable
        st.session_state["linktable"] = linktable
        st.session_state["parents"] = parents

handover()

if "csvoutput" not in st.session_state:
    st.session_state["csvoutput"] = False
    st.session_state["output_state"] = False

if "pages_tag_data" not in st.session_state: st.session_state["pages_tag_data"] = {}
if "pages_word_data" not in st.session_state: st.session_state["pages_word_data"] = {}

if not "timer" in st.session_state:
    st.session_state["timer"] = {
        'start_str' : '--:--:--',
        'end_str' : '--:--:--',
        'elapsed_str' : '--:--:--',
        
        'start_dt' : None,
        'end_dt' : None
    }
    


### formlist
g.default_formlist = [
    ["http://ac0f2ce0f.mbsdcc2023exam.net/sns/login.php",
        ["/html/body/div[2]/div/div/div/form/fieldset/input[1]",0,"koralcyon0"],
        ["/html/body/div[2]/div/div/div/form/fieldset/input[2]",0,"koralcyon0"],
        ["/html/body/div[2]/div/div/div/form/fieldset/button",5,True]
    ],
    [
        "http://ac0f2ce0f.mbsdcc2023exam.net/crammer/login/",
        ["/html/body/div/div/div/div[1]/main/div/div/div/div/div[3]/div[2]/form/div[1]/div[2]/div[1]/div/input",0,"student1"],
        ["/html/body/div/div/div/div[1]/main/div/div/div/div/div[3]/div[2]/form/div[2]/div[2]/div[1]/div[1]/input",0,"student1"],
        ["/html/body/div/div/div/div[1]/main/div/div/div/div/div[3]/div[2]/form/div[3]/button",5,True]
    ],
    [
        "http://ac0f2ce0f.mbsdcc2023exam.net/market/login.php",
        ["/html/body/div/div/div[2]/form/fieldset/input[1]",0,"koralcyon0"],
        ["/html/body/div/div/div[2]/form/fieldset/input[2]",0,"koralcyon0"],
        ["/html/body/div/div/div[2]/form/fieldset/input[3]",5,True]
        
    ],
    [
        "http://ac0f2ce0f.mbsdcc2023exam.net/market/product.php?mode=make&id=new",
        ["/html/body/div/div/div[2]/form/fieldset[1]/input", 0, "a"],
        ["/html/body/div/div/div[2]/form/fieldset[3]/textarea",0,"a"],
        ["/html/body/div/div/div[2]/form/fieldset[4]/input",0,"10"],
        ["/html/body/div/div/div[2]/button",5,True]
    ],
    [
        "http://ac0f2ce0f.mbsdcc2023exam.net/sns/login.php",
        ["/html/body/div[2]/div/div/div/form/fieldset/input[1]",0,"hatomato"],
        ["/html/body/div[2]/div/div/div/form/fieldset/input[2]",0,"Hatomato."],
        ["/html/body/div[2]/div/div/div/form/fieldset/button",5,True]
    ],
    [
        "http://ac0f2ce0f.mbsdcc2023exam.net/crammer/login/",
        ["/html/body/div/div/div/div[1]/main/div/div/div/div/div[3]/div[2]/form/div[1]/div[2]/div[1]/div/input",0,"admin"],
        ["/html/body/div/div/div/div[1]/main/div/div/div/div/div[3]/div[2]/form/div[2]/div[2]/div[1]/div[1]/input",0,"admin"],
        ["/html/body/div/div/div/div[1]/main/div/div/div/div/div[3]/div[2]/form/div[3]/button",5,True]
    ],
    [
        "http://ac0f2ce0f.mbsdcc2023exam.net/market/login.php",
        ["/html/body/div/div/div[2]/form/fieldset/input[1]",0,"hato"],
        ["/html/body/div/div/div[2]/form/fieldset/input[2]",0,"hato"],
        ["/html/body/div/div/div[2]/form/fieldset/input[3]",5,True]
    ],
    [
        "http://ac0f2ce0f.mbsdcc2023exam.net/market/product.php?mode=show&id=1",
        ["/html/body/div/div/div[2]/form/input[1]",0,"a"],
        ["/html/body/div/div/div[2]/form/input[2]",5,True],
        ["/html/body/div/div/div[2]/form/input[2]",5,True]
    ],
    [
        "http://ac0f2ce0f.mbsdcc2023exam.net/market/userlist.php",
        ["/html/body/div/div/div[2]/form[1]/input[1]",0,"aaaaaa"],
        ["/html/body/div/div/div[2]/form[1]/input[2]",5,True]
    ],
    [
        "http://ac0f2ce0f.mbsdcc2023exam.net/market/charge.php",
        ["/html/body/div/div/div[2]/div/div[1]/input",0,"1000000"],
        ["/html/body/div/div/div[2]/div/div[1]/button",5,True]
    ]
]
iff.form_setup()

#ディレクトリやファイル、そして**Json出力**を司る関数
def makeDir_makeJson (newPath, pageFileName, tableFileName):
    all_page = st.session_state["all_page"]
    global idtable
    global linktable
    
    #パスまでのディレクトリを生成
    os.makedirs( newPath, exist_ok=True )
    
    
    # 指定したjsonファイルを書き込みモードで開く（見つからなかったら新規作成もしてくれる）
    with open( os.path.join( newPath,pageFileName ), "w", encoding="utf-8" ) as file:
        # 辞書型explored_pageを.jsonに保存しちゃう　めっちゃめちゃ大事な一行
        json.dump( all_page, file, ensure_ascii=False )
        
    # idtableとlinktableを統合し、一つのjsonファイルに纏めて保存する
    datatable = {
        "getid" : st.session_state[ "idtable" ],
        "geturl": st.session_state[ "linktable" ],
        "parents": st.session_state[ "parents" ]
    }
    with open( os.path.join( newPath,tableFileName ),"w", encoding="utf-8" ) as file:
        json.dump( datatable, file, ensure_ascii=False )

def delete_crawlresult(path):
    shutil.rmtree( path )
    print("crawlresult deleted")


#大きい区切りはタブで分ける！！
tab_main, tab_lists, tab_data = st.tabs(["Main/option","per-page settings", "crawl data"])

#-tab------------------------------------------------------------------------------------------#
#//////////////////////////////////////////////////////////////////////////////////////////////#
#----------------------------------------------------------------------------------------------#


with tab_lists:

    
    
    ### formlist
    
    iff.open_form()

    ### blacklist
    iff.open_blacklist()

    ### tag_pick_up_chisenon
    iff.open_taglist()
    
    ### certain_word_pickup
    iff.open_wordfinder()
    

#-tab------------------------------------------------------------------------------------------#
#//////////////////////////////////////////////////////////////////////////////////////////////#
#----------------------------------------------------------------------------------------------#

#実行オプション（フロント）#######################################################
with tab_main:
    st.header("crawling")
    st.write("---")

    place_scantimespan = st.empty()
    place_most_contain = st.empty()
    place_startlink = st.empty()
    place_crawllimit = st.empty()
    place_chromedriverpath = st.empty()
    
    # timespanを設定 #####
    time_span = 0.5
    col0,col1,col2 = place_scantimespan.columns([4, 12, 1.5])
    col0.text("Scan time span") #タイトル
    time_span = col1.number_input(label='Scan time span',value= 0.50,label_visibility="collapsed")
    col2.button(":question:", key="timespan_help", help="クローラーが次のページにアクセスするまでの時間を設定します。単位は秒です。")

    # most_containを設定 #####
    col0,col1,col2 = place_most_contain.columns([4, 12, 1.5])
    if "url_most_contain_caution_toggle" not in st.session_state: st.session_state["url_most_contain_caution_toggle"] = False
    col0.text("URL most contains") #タイトル
    root= most_contain = col1.text_input(value='//ac0f2ce0f.mbsdcc2023exam.net/' ,label='most_contain URL', label_visibility="collapsed")
    with col2: #ボタン
        if st.button(":question:", key="most_contain_caution", help=
                     "この文字列を含まないリンクへはアクセスしません。 空白にするとstart URLが代わりに利用されます。"):
            st.session_state["url_most_contain_caution_toggle"] = not st.session_state["url_most_contain_caution_toggle"]
    #if st.session_state["url_most_contain_caution_toggle"] == True :
        #st.write("")


    #ここから探索を開始 ###
    col0,col1,col2 = place_startlink.columns([4, 12, 1.5])
    col0.text("crawlstart URL") #タイトル
    startlink = col1.text_input(value='http://ac0f2ce0f.mbsdcc2023exam.net/',label='start URL',
                                label_visibility="collapsed") 
    col2.button(":question:", key="crawlstart_help", help="ここに入力したURLから探索が始まります。 空白にするとroot URLが代わりに利用されます。")

    # most_containとstartlinkの整合性を確認
    if most_contain == "" and startlink == "":
        st.error("most_contain url又はstart url少なくとも一か所入力してください")
        most_contain = "http://example.jp/"
        startlink = most_contain
    elif most_contain == "" or startlink == "":
        if most_contain == "": most_contain = startlink
        else: startlink = most_contain
    
    #探索ページ上限　#####
    col0,col1,col2 = place_crawllimit.columns([4, 12, 1.5])
    col0.text("limit explore count") #タイトル
    limit_explore = col1.number_input(placeholder=-1, value=-1,label='limit explore count',
                                    label_visibility="collapsed")
    col2.button(":question:", key="crawllimit_help", help="探索するページ数の上限を設定します。 マイナス値で無限になり、探索しうる全ページにアクセス後終了します。")

    #driverのパスを指定 ########
    if "driver_caution_toggle" not in st.session_state: st.session_state["driver_caution_toggle"] = False
    
    col0,col1,col2 = place_chromedriverpath.columns([4, 12, 1.5])
    col0.text("chromedriver path") #タイトル
    driver_path = col1.text_input(label="chromedriver path",placeholder=R"path\to\chromedriver",label_visibility="collapsed")
    with col2:
        if st.button(":warning:", key="driverpath_help", help="chromedriverのパスを指定します。  ※注意｜展開/閉じる"):
            st.session_state["driver_caution_toggle"] = not st.session_state["driver_caution_toggle"]
    if st.session_state["driver_caution_toggle"] == True :
        st.write("""> chromedriverのパスについて\n
    このプログラムではchromedriverを使用しています。
    ご利用のChromeバージョンに対応したChromedriverをダウンロードし、Pathを指定してください。
    ※ パス末尾には"\chromedriver" を含めて入力してください。
    なおオンライン環境の場合、「download_chromedriver.py」を実行することで、自動で対応driverをダウンロードできます。
    """)
    if driver_path.startswith('"') and driver_path.endswith('"'): driver_path = driver_path[1:-1]
    if not driver_path.endswith(".exe") : driver_path += ".exe" #拡張子を付ける
    
    if driver_path == "":
        st.error("driver pathを入力してください")
    elif os.path.exists(driver_path) == False:
        st.error("chromedriverが見つかりませんでした。パスを確認してください。")
    
    # 実行オプション２ ###########################################################
    
    col0,col1 = st.columns([1,1])
    
    do_auto_output = col0.toggle("auto output",value=True,help="クロール終了時に自動で出力します。")
    
    op_get_images = col1.toggle("get images",value=True,help="html内で参照された画像を取得します。")
    #op_scan_images = st.toggle("scan images",value=True,help="画像内の文字を認識します。", disabled=not op_get_images)
    
    # 実行 ###################################################################################################

    #出力オプション
    g.output_path = os.path.join( os.path.dirname( os.path.abspath(__file__) ), 'crawlresult') #出力パスの指定。
    jsonOut_fileName = "crawled_pages.json" #出力するファイル名
    idurL_linktable_filename = "id_url_linktable.json" #ファイル構造再現の時に使いたいので、別ファイルに保存する

    # もしst.session_state["crawlRunnigToggle"]に中身がないならFalseを入れる
    if "crawlRunnigToggle" not in st.session_state:
        st.session_state["crawlRunnigToggle"] = False #トグル初期化

    # crawl_status_place を設置 
    crawl_status_place = st.empty()

    # タイマー表示
    
    def now() : return datetime.datetime.now().replace(microsecond=0)
    def refresh_timer():
        
        
        timerdict = st.session_state["timer"]
        
        if timerdict['start_dt'] !=None:
            timerdict['start_str'] = timerdict['start_dt'].strftime(r'%m/%d %H:%M:%S')
            timerdict['elapsed_str'] = now() - timerdict['start_dt']
        
        if timerdict['end_dt'] !=None: #動作してくれない、なんで
            timerdict['end_str'] = timerdict['end_dt'].strftime(r'%m/%d %H:%M:%S')
            timerdict['elapsed_str'] = timerdict['end_dt'] - timerdict['start_dt']
        
        timer_start.write(f"start: {timerdict['start_str']}")
        timer_end.write(f"end: {timerdict['end_str']}")
        timer_elapsed.write(f"elapsed: {timerdict['elapsed_str']}")
        
        st.session_state["timer"] = timerdict


    #defでクロール部分を関数にする
    def crawle(limit_explore,time_span):

        crawl_status_place.error("初期化中...")
        
        #入力を無効化する        
        place_scantimespan.number_input(label='Now crawling...',value=time_span,disabled=True)
        place_most_contain.text_input(label='most_contain URL_',value=most_contain,label_visibility="collapsed",disabled=True)
        place_startlink.text_input(label='start URL_',value=startlink,label_visibility="collapsed",disabled=True)
        place_crawllimit.number_input(label='limit explore count_',value=limit_explore,label_visibility="collapsed",disabled=True)
        place_chromedriverpath.text_input(label="chromedriver path_",value=driver_path,label_visibility="collapsed",disabled=True)

        
        # クローラーが動いていることを示すトグル
        st.session_state["crawlRunnigToggle"] = True
        st.session_state["crawlRunnigNow"] = True
        reset()
        handover()
        delete_crawlresult(g.output_path)
        
        #初期設定 構造データ,出力パス
        linktable.append(startlink)
        idtable[startlink] = 0
        url_found.add(startlink)
        parents[0] = -1
        id_not_explored.append( 0 )
        
        #アクセス回数上限は3回
        perURL_access = {0:0} #id : アクセス回数
        
        #クキー
        cookie_jar = None
        
        my_bar = st.progress(0)
        crawling_info_url = st.empty()
        crawling_info = st.empty()
        if "pages_tag_data" not in st.session_state: st.session_state["pages_tag_data"] = {}
        if "pages_word_data" not in st.session_state: st.session_state["pages_word_data"] = {}
        
        os.makedirs( os.path.join( g.output_path, "ids", "0" ), exist_ok=True )

        url_explored = 0 # 探索済みのURL数をカウントする
        url_noexp = 0 # 探索対象外のURL数をカウントする
        
        crawl_status_place.error("chromedriver起動中...")
        
        #selenium用のdriverを起動
        cService = Service(executable_path=driver_path)
        g.driver = webdriver.Chrome(service=cService)
        
        
        #ネストdef 新しく見つけたかもしれないリンクを判断、追加する
        def newpage(absolute_link):
            nonlocal url_noexp
            newpage_id = -1 #仮
            
            # 取得したURLのうちurl_foundに含まれていない新発見URLを、url_not_exploredに追加
            if not ( absolute_link in url_found ):
                newpage_id = len(linktable)
                target_state = -1 #仮 
                
                #rootから外れておらず、行ってもいいリンクか？
                if most_contain in absolute_link and not (absolute_link in g.blacklist):  
                    #行っていいリンクなら、アクセスキューに追加、”未探索”タグを付与　※実際に探索された際、”探索済”タグに置き換わる
                    id_not_explored.append ( newpage_id )
                    target_state = 1
                else:
                    #行ってはいけないなら、キュー追加はせず”探索対象外”タグを付与
                    target_state = 2
                    url_noexp += 1
                
                #さらに発見済みリンクテーブル等にも記録。あとでURLやIDを参照しやすくする。
                url_found.add( absolute_link )
                linktable.append( absolute_link )
                idtable[absolute_link] = newpage_id
                
                # url,id,expStateのみ判明したページデータをPage()を使ってまとめ、記録しておく
                all_page[newpage_id] = Page(absolute_link,newpage_id,[],[],target_state,{}).data
                perURL_access[newpage_id] = 0
                print("new page found! id:"+str(newpage_id)+",url:"+absolute_link+"\n")
            else: #既に発見済みの場合、定義されたIDを持ってくる
                newpage_id = idtable[absolute_link]
                
                #if perURL_access[newpage_id] < 3:
                #    id_not_explored.append( newpage_id )
                #    perURL_access[newpage_id] += 1
                #    print(f"re-access page! id:{newpage_id},url:{absolute_link}, count->{perURL_access[newpage_id]}\n")

            # 取得したURLをdirect/farで分け、どっちかのリストに追加
            url1 = urlparse(current_url).path[:-1]
            url2 = urlparse(absolute_link).path[:-1]
            if absolute_link.startswith(current_url) and url1.count("/") +1 == url2.count("/"):
                dirChild.append(newpage_id)
                parents[newpage_id] = current_id
            else:
                farChild.append(newpage_id)
                
            # crawlresultに、対応するIDのフォルダを作成
            os.makedirs( os.path.join( g.output_path, "ids", str(newpage_id) ), exist_ok=True )
        
            return newpage_id
        
        #探索RTAはっじまっるよー
        while len( id_not_explored ) > 0 and limit_explore != 0:
            
            #Pageインスタンス生成準備：キューからURL取り出し、今回探索したページのIDを設定
            current_id = id_not_explored.popleft() #dequeue
            current_url = linktable[current_id]
            dirChild = [] #list
            farChild = [] #list
            print("id:"+str(current_id)+",url:"+current_url+"\n")
            
            
            # progress bar
            my_bar.progress( url_explored/(len(url_found)+1) ,text=f"run:{url_explored}/{len(url_found)}" )
            
            crawling_info_url.write(f"url: {current_url}")
            crawling_info.write("")
            
            response_message = {} #レスポンスから、ステータスコードやテキストフレーズを保存
            try:
                if current_url in g.blacklist:
                    raise Exception("blacklisted")
                response = requests.get(current_url, timeout=5, cookies=cookie_jar)
                # ステータスコードとテキストフレーズを取得、response_messageに格納（あとでjsonにまとめる）
                response_message["status_code"] = response.status_code
                response_message["text_phrase"] = response.reason
                html_content = response.text
                
                word_result = iff.wordcount(str(response_message))
                if word_result != 0:
                    st.session_state["pages_word_data"][f"{current_id}_responce"] = word_result
                
                
                response.raise_for_status()  # エラーコードが含まれていれば中断し、例外-exceptを発生させる

                # ここで正常なレスポンスの処理を行う
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                crawling_info.write(f"success: {response_message['status_code']} {response_message['text_phrase']}")
                
                # すべてのaタグを取得、うち有効なhrefについて処理を実行
                links = soup.find_all('a')
                for link in links:
                    href = link.get('href')
                    if href and not href.startswith('#'):
                        absolute_link = urljoin(current_url, href) #見つかった、対象のリンク
                        newpage(absolute_link)
                    
                # selenium自動入力    
                if iff.find_whether_url_formset(current_url) != -1:
                    autoenter_back = iff.auto_enter(current_url)
                    
                    cookie_dict = {cookie['name']: cookie['value'] for cookie in autoenter_back["cookie"]}
                    cookie_jar = requests.cookies.RequestsCookieJar()
                    cookie_jar.update(cookie_dict)
                    
                    #hrefと同様に、新発見URLをurl_not_exploredに追加
                    absolute_link = autoenter_back["url"] #見つかった、対象のリンク
                    newpage_id = newpage(absolute_link)
                    
                    #前のURLにも再度アクセス
                    if current_id in parents:
                        id_not_explored.append( parents[current_id] )
                        url_explored -= 1
                    
                    #word受け取り
                    if autoenter_back["word"] != 0:
                        st.session_state["pages_word_data"][f"{newpage_id}_selenium"] = autoenter_back["word"]
                
                # chiseのタグ抽出
                tag_counts = iff.tagCounterchisenon(soup)
                st.session_state["pages_tag_data"][current_id] = {"id":current_id, "url":current_url, "data":tag_counts}
                
                # wordfinderのワード抽出
                word_counts = iff.wordcount(html_content)
                st.session_state["pages_word_data"][current_id] = word_counts
                
                # 画像取得
                if op_get_images == True:
                    import image_functions as imgf
                    imgf.getimages(soup,current_url, current_id)
                    
                    #if op_scan_images == True:
                    #    imgf.ocr_all_images_in_folder('MBSD{')
                
                #各ファイルを出力
                iff.csvoutput(csv_filepath=f"ids/{current_id}" ,key=current_id)
                
                with open( os.path.join( g.output_path, "ids", str(current_id), "page.html" ), "w", encoding="utf-8" ) as file:
                    file.write( html_content )
                    
                
            # request.get()した際、アクセスできなかった場合
            except requests.exceptions.RequestException as e:
                # 例外が発生した場合の処理を行う
                print("Webページにアクセスできませんでした:", e)
                crawling_info.write(f"failed: {e}")
                
            # url,id,dirChild,farChildなどのデータをPage()を使ってまとめ、完成形としてdict型で出力用のexplored_pageに記録する
            all_page[current_id] = Page(current_url,current_id,dirChild,farChild,0,response_message).data
            
            if perURL_access[current_id] == 0:
                url_explored += 1

            # クローラー実行中の表示
            if st.session_state["crawlRunnigToggle"] == True:
                if st.session_state["crawlRunnigNow"] == True:
                    crawl_status_place.error(Exception('クローラー実行中... 実行中はいずれのボタンも押さないでください'))
                    st.session_state["crawlRunnigNow"] = False
            
            # url,id,dirChild,farChildなどのデータをPage()を使ってまとめ、完成形としてdict型で出力用のexplored_pageに記録する
            all_page[current_id] = Page(current_url,current_id,dirChild,farChild,0,response_message).data
            
            time.sleep(time_span)
            limit_explore -= 1
            refresh_timer()

            #endwhile 次の未探索URLにアクセスしにいく
            
        st.session_state["all_page"] = all_page
        st.session_state["linktable"] = linktable
        st.session_state["idtable"] = idtable
        st.session_state["parents"] = parents
        print("##### crawl finished #####")
        
        st.session_state["timer"]["end_dt"] = now()
        st.session_state["crawlRunnigToggle"] = "done"
        st.rerun()


    #ボタンを押すとクローラーが動くようにする

    
    # timer
    timer_start = st.empty()
    timer_end = st.empty()
    timer_elapsed = st.empty()
    
    if st.button('start crawler',
                type=("primary" if st.session_state["crawlRunnigToggle"] == False else "secondary"),
                use_container_width=True,
                disabled= os.path.exists(driver_path) == False):
        
        #始めた時間
        st.session_state["timer"]["start_dt"] = now()
        st.session_state["timer"]["end_dt"] = None

        crawle(limit_explore,time_span)
        
        st.session_state["timer"]["end_dt"] = now()
        
        refresh_timer()
        st.rerun()
        
        #クローラーが動いたことあるかの判定をTrueにする
        crawler_has_worked = True
        st.session_state["crawler_has_worked"] = crawler_has_worked


    # クローラーの実行状況表示
    if st.session_state["crawlRunnigToggle"] == False:
        crawl_status_place.warning("クロール未実行")
    elif st.session_state["crawlRunnigToggle"] == "done":
        crawl_status_place.success("クロール完了")


    def result():
        all_page = st.session_state["all_page"]
        print("result:\n")
        print(all_page)
        print("total pages:"+str(len(all_page)))
        #アクセス失敗したページ数も数えるべき
    

    outputcrawlresult = st.empty()
    g.output_state = st.empty()
    g.csv_output_state = st.empty()
    
    
    
    if outputcrawlresult.button('output crawl result',
                type=("secondary" if st.session_state["crawlRunnigToggle"] == False else "primary"),
                use_container_width=True) or\
       (do_auto_output == True and st.session_state["crawlRunnigToggle"] == "done" and st.session_state["output_state"] != "done"):
        
        g.output_state.error("探索データを保存中...")
        makeDir_makeJson(g.output_path, jsonOut_fileName, idurL_linktable_filename)
        print("###json output done!\n")
        
        # ファイル構造再現
        g.output_state.error("ファイル構造を再現中...")
        import filetree_reproduce
        filetree_reproduce.filetree_reproduce()
        print("###filetree reproduce done!\n")
        
        if "pages_tag_data" in st.session_state:
            g.csv_output_state.error("tag dataを保存中...")
            iff.csvoutput(csv_filepath="")
            g.csv_output_state.info(R"tag data出力完了")
        else:
            g.csv_output_state.error("エラー: tag dataがありません")

        st.session_state["output_state"] = "done"
    
    if st.session_state["output_state"] == "done":
        g.output_state.success(R"出力完了( .\crawlresult\reproduce )")

    refresh_timer()
    

#-tab------------------------------------------------------------------------------------------#
#//////////////////////////////////////////////////////////////////////////////////////////////#
#----------------------------------------------------------------------------------------------#

with tab_data:
    
    #with st.expander("all_page"):
    #    st.write(st.session_state["all_page"])
    #with st.expander("linktable"):
    #    st.write(st.session_state["linktable"])
    #with st.expander("idtable"):
    #    st.write(st.session_state["idtable"])
    #with st.expander("parents"):
    #    st.write(st.session_state["parents"])
    
    #st.divider()
    
    def get_expstate(state):
        if state == 0:
            return "探索済"
        elif state == 1:
            return "未探索"
        elif state == 2:
            return "探索対象外"
        else:
            return "value error"
    
    col0,col1,col2 = st.columns([4, 12, 1.5])
    col0.text("page id")
    with col1:
        search_id = st.number_input(label='page id',value=0,label_visibility="collapsed",format="%d")
    col2.button(":mag:", key="pageid_search", help="指定したidのページを表示します。")
    if search_id != None:
        all_page = copy.deepcopy(all_page)
        if search_id in all_page:
            pagedatatxt = f"ページid {search_id}...\n"
            pagedatatxt += f"URL: {st.session_state['linktable'][search_id]}\n"
            pagedatatxt += f"探索状況: {all_page[search_id]['expState']}|{get_expstate(all_page[search_id]['expState'])}\n"
            pagedatatxt += f"responce: {all_page[search_id]['response_message']}\n"
            st.text(pagedatatxt)
            
            with st.expander(f'direct children({len(all_page[search_id]["dirChild"])})'):
                for childid in all_page[search_id]["dirChild"]:
                    st.text (f"{childid}|{ get_expstate(all_page[childid]['expState']) } : {st.session_state['linktable'][childid]}")
            with st.expander(f'far children({len(all_page[search_id]["farChild"])})'):
                for childid in all_page[search_id]["farChild"]:
                    st.text (f"{childid}|{ get_expstate(all_page[childid]['expState']) }  : {st.session_state['linktable'][childid]}")
            if search_id in st.session_state["parents"]:
                st.text(f"parent: {st.session_state['parents'][search_id]} : {st.session_state['linktable'][st.session_state['parents'][search_id]]}")
            else:
                st.write("parent: could not identify")
            
        else:
            st.error(f"page id {search_id} is not found")
    
    #----------------------------------
            
    st.write("---")
    st.header(f"total pages")
    
    st.write(f"found: {len(st.session_state['all_page'])}")
    st.write(f"explored: {len([i for i in st.session_state['all_page'] if st.session_state['all_page'][i]['expState'] == 0])}")
    
    
    with st.expander("wordfinder"):
        worddata = copy.deepcopy(st.session_state["pages_word_data"])
        st.write( { i: worddata[i] for i in worddata if worddata[i] != 0})
        
    with st.expander("linktable"):
        st.write(st.session_state["linktable"])
    with st.expander("idtable"):
        st.write(st.session_state["idtable"])