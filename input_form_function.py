import streamlit as st
import copy #配列のコピー
import global_value as g
from selenium import webdriver
#from selenium.webdriver.common.keys import Keys
#from selenium.webdriver.chrome import service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
import re, os, csv, time

#含まれているもの
#formlist
#blacklist
#selenium


### formlist ####################################################################################################

def f_save_rerun():
    st.session_state["formlist"] = copy.deepcopy( g.formlist )
    st.session_state["editing"] = g.editing
    st.rerun()


#変幻自在な要素を作るよ。
def f_variable_line( i=-1, j=-1, type="x-c" ):
    #type.. addurl, addx-c, url, x-c  #addがついてるやつは、追加ボタン　それ以外は表示ライン
    #editing.. {i}-{j}, *{i}-{j}  #*つきは削除確認モード　ついてないやつは編集モード j=0はURLを意味する
    
    #削除確認モード
    if g.editing[0] == "*" and g.editing[1:] == f"{i}-{j}":
        #URL
        if j == 0:
            col0,col1,col2,col3,col4,col5 = st.columns([2, 8, 3, 1, 1, 1]) #足して16 
            col0.markdown(f'<div style="text-align:right; color:#7f7f7f; font-family:monospace;">Page URL:</div>',unsafe_allow_html=True)
            col1.text(f'{st.session_state["formlist"][i][0]}')
            col2.markdown(':wastebasket: delete?')
            with col3:
                if st.button(":white_check_mark: ", help="confirm"):
                    del g.formlist[i]
                    g.editing = "none"
                    f_save_rerun()
            with col4:
                if st.button(":x: ", help="cancel"):
                    g.editing = "none"
                    f_save_rerun()
            col5.markdown(f"#{i}")
        #xpath-content
        else:
            this_type = g.formlist[i][j][1]
            col0,col1,col2,col3,col4,col5,col6,col7 = st.columns([0.5, 1.5, 4, 2.5, 2, 3, 1, 1]) #足して15.5 
            col0.text(f"{j}")
            col1.markdown(f'<div style="text-align:right; color:#7f7f7f; font-family:monospace;">Xpath:</div>',unsafe_allow_html=True)
            col2.text(f'{st.session_state["formlist"][i][j][0]}')
            col3.markdown(f'<div style="text-align:right; color:#ff4b4b; font-family:monospace;">\
                          {g.input_types[ st.session_state["formlist"][i][j][1] ]}: </div>',unsafe_allow_html=True)
            with col4:
                if this_type == 0:
                    st.text(f'{st.session_state["formlist"][i][j][2]}')
                elif this_type <= 2:
                    st.text(f'select: {st.session_state["formlist"][i][j][2]}')
                elif this_type == 3:
                    st.text(f'index - {st.session_state["formlist"][i][j][2]}')
                elif this_type == 5:
                    st.text("<Submit>")
            col5.markdown(':wastebasket: delete?')
            with col6:
                if st.button(":white_check_mark: ", help="confirm"):
                    del g.formlist[i][j]
                    g.editing = "none"
                    f_save_rerun()
            with col7:
                if st.button(":x: ", help="cancel"):
                    g.editing = "none"
                    f_save_rerun()
            if this_type == 4:
                with st.expander("textarea input...",expanded=True):
                    st.write( st.session_state["formlist"][i][j][2] )
            
    #編集中 入力フォーム
    elif g.editing==f"{i}-{j}" or g.editing==type:
        #URL
        if type.endswith("url") or j == 0:
            col0,col1,col2,col3 = st.columns([13, 1, 1, 1]) #計16
            with col0:
                g.formlist[i][0] = st.text_input(f"inurl{i}",value=g.formlist[i][0], placeholder="page url here...",label_visibility="collapsed")
            with col1:
                if st.button(":white_check_mark:",key=f"x-c-ok{i}-{j}", help="confirm"):
                    g.editing = "none"
                    f_save_rerun()
            with col2:
                if st.button(":x: ", help="cancel"):
                    g.editing = "none"
                    g.formlist = copy.deepcopy( st.session_state["formlist"] )
                    f_save_rerun()
            col3.markdown(f"#{i}")
                    
                
        #xpath-content入力
        else:
            col0,col1,col2,col3,col4,col5 = st.columns([1, 4, 3.5, 5.5, 1, 1]) #計16
            col0.text(f"{j}")
            with col1:
                g.formlist[i][j][0] = st.text_input(f"xpath{i}-{j}",value=g.formlist[i][j][0], placeholder="xpath here...",label_visibility="collapsed")
            with col2:
                g.formlist[i][j][1] = g.input_types.index( st.selectbox(f'type{i}-{j}',g.input_types,label_visibility='collapsed', index=g.formlist[i][j][1]) )
                this_type = g.formlist[i][j][1]
            with col3:
                if this_type == 0:
                    if not isinstance( g.formlist[i][j][2] ,str) : g.formlist[i][j][2] = "content"
                    g.formlist[i][j][2] = st.text_input(f"text{i}-{j}",value=g.formlist[i][j][2], placeholder="content here...",label_visibility="collapsed")
                elif this_type == 1 or this_type == 2:
                    if not isinstance( g.formlist[i][j][2] ,bool) : g.formlist[i][j][2] = True
                    g.formlist[i][j][2] = st.toggle(f"whether click",value=g.formlist[i][j][2],key=f'toggle{i}-{j}')
                elif this_type == 3:
                    if not isinstance( g.formlist[i][j][2] ,int): g.formlist[i][j][2] = 0
                    subcol0,subcol1 = st.columns([1,2])
                    subcol0.text("index-")
                    with subcol1:
                        g.formlist[i][j][2] = st.number_input(f"dropdown_index{i}-{j}",step=1,min_value=0,format=r"%d",value=g.formlist[i][j][2],label_visibility='collapsed')
                elif this_type == 4:
                    if not isinstance( g.formlist[i][j][2] ,str): g.formlist[i][j][2] = "content"
                elif this_type == 5:
                    g.formlist[i][j][2] = True
                    st.text("<Submit>")

            with col4:
                if st.button(":white_check_mark:",key=f"x-c-ok{i}-{j}", help="confirm"):
                    g.editing = "none"
                    f_save_rerun()
            with col5:
                if st.button(":x: ", help="cancel"):
                    g.editing = "none"
                    g.formlist = copy.deepcopy( st.session_state["formlist"] )
                    f_save_rerun()
            if this_type == 4:
                g.formlist[i][j][2] = st.text_area("textarea input...", value=g.formlist[i][j][2])
    
    #not編集中、通常時(表示や追加ボタン動作)
    else:
        
        if type=="x-c":
            this_type = g.formlist[i][j][1]
            col0,col1,col2,col3,col4,col5,col6 = st.columns([0.5, 1.5, 4.8, 1.7, 5, 1, 1]) #足して16
            col0.text(f'{j}')
            col1.markdown(f'<div style="text-align:right; color:#7f7f7f; font-family:monospace;">Xpath:</div>',unsafe_allow_html=True)
            col2.text(f'{st.session_state["formlist"][i][j][0]}')
            col3.markdown(f'<div style="text-align:right; color:#ff4b4b; font-family:monospace;"> {g.input_types[ st.session_state["formlist"][i][j][1] ]}: </div>',unsafe_allow_html=True)
            
            with col4:
                if this_type == 0:
                    st.text(f'{st.session_state["formlist"][i][j][2]}')
                elif this_type <= 2:
                    st.text(f'select:{g.formlist[i][j][2]}')
                elif this_type == 3:
                    st.text(f'index- {st.session_state["formlist"][i][j][2]}')
                elif this_type == 5:
                    st.text("<Submit>")
            with col5:
                if st.button(":lower_left_fountain_pen:",key=f"editx-c{i}-{j}", help="edit"):
                    g.editing = f"{i}-{j}"
                    f_save_rerun()
            with col6:
                if st.button(":wastebasket:",key=f"delx-c{i}-{j}", help="delete"):
                    #del formlist[i][j] #やっぱdelしないでワンクッション置く
                    g.editing = f"*{i}-{j}" #先頭に*をつけたら削除確認モード
                    f_save_rerun()
            if this_type == 4:
                with st.expander("textarea input...",expanded=True):
                    st.write( st.session_state["formlist"][i][j][2] )
            
        elif type=="addx-c":
            if st.button(":heavy_plus_sign: add xpath-content",key=f"addx-c{i}"):
                g.formlist[i].append(["xpath",0,"content"])
                g.editing = f"{i}-{ len(g.formlist[i])-1 }"
                f_save_rerun()
            
        elif type=="url":
            col0,col1,col2,col3,col4 = st.columns([2, 11, 1, 1, 1]) #足して16
            col0.markdown(f'<div style="text-align:right; color:#7f7f7f; font-family:monospace;">Page URL:</div>',unsafe_allow_html=True)
            col1.text(f'{st.session_state["formlist"][i][0]}')
            with col2:
                if st.button(":lower_left_fountain_pen:",key=f"editurl{i}", help="edit"):
                    g.editing = f"{i}-0"
                    f_save_rerun()
            with col3:
                if st.button(":wastebasket:",key=f"delurl{i}", help="delete"):
                    g.editing = f"*{i}-{j}" #確認モードへ
                    f_save_rerun()
            col4.markdown(f"#{i}")
                
        elif type=="addurl":
            if st.button(":heavy_plus_sign: add page URL"):
                g.formlist.append(["url"])
                g.editing = f"{len(g.formlist)-1}-0"
                f_save_rerun()
    

def form_setup():
    
    
    g.input_types = ['text','radio','check','dropdown','textarea','submit']
    
    # session_stateを新規作成/読み込む
    if "formlist" not in st.session_state:
        st.session_state["formlist"] = g.default_formlist
        st.session_state["editing"] = "none"
        
    g.formlist = copy.deepcopy( st.session_state["formlist"] )
    g.editing = st.session_state["editing"]


#formlistのデータ構造に沿って、variable_lineを表示するだけ
def open_form():
    
    st.header("forms auto enter")
    #st.write("---")
    #大index
    for i in range( len(g.formlist) ):
        #小index
        if len(g.formlist[i]) == 1 and g.editing != f"{i}-0":
            st.warning("Warning: Any Xpath not set!")
        
        for j in range( len(g.formlist[i]) ):
            f_variable_line(i,j,type=( "url" if j==0 else "x-c"))
            
        f_variable_line(i,type="addx-c")
        st.caption("Please don't forget to set 'submit' button at the end!")
        st.write("---")
    f_variable_line(type="addurl")
    st.write("---")
    
    g.formlist_urls = {}
    for i in range( len(g.formlist) ):
        g.formlist_urls[ g.formlist[i][0] ] = i

### blacklist ####################################################################################################

def open_blacklist():
    st.header("blacklist")
    blackinput = st.text_area("blacklist", label_visibility="collapsed", 
                            value="http://ac0f2ce0f.mbsdcc2023exam.net/market/admin.php\n\
https://www.mbsd.jp/\n\
http://ac0f2ce0f.mbsdcc2023exam.net/market/logout.php")
    g.blacklist = list(dict.fromkeys( re.split(r"[\n]+", blackinput) ))
    if "" in g.blacklist: g.blacklist.remove("")
    
    col0,col1 = st.columns([15,1])
    col0.text(f"total: {len(g.blacklist)}")
    col1.button(":question:", help="入力は改行で区切ってください")

### selenium ###############################################################################################



def find_whether_url_formset(current_url):
    for i in range(len(g.formlist)):
        if current_url == g.formlist[i][0]:
            return i
    return -1 #なんも見つかんなかったっす

def newtab_and_switch():

    # 新しいタブを作り、開く。
    # ウィンドウのリスト(handles)の、タブ追加前/後を比較し、新規でできたとされる要素を判別する
    before_handles = g.driver.window_handles
    before_len = len(g.driver.window_handles)

    g.driver.switch_to.new_window("tab")
    WebDriverWait(g.driver, 10).until(lambda d: len(d.window_handles) > before_len) #

    after_handles = g.driver.window_handles
    newhandle = set(after_handles).difference(set(before_handles)).pop()
    g.driver.switch_to.window(newhandle)
    
    return newhandle #str タブの整理番号みたいなやつなので保存できるように

def switchtab(handle):
    g.driver.switch_to.window(handle)


def auto_enter(url): #driverの起動を関数で行うと、関数が終わった時勝手に閉じるっぽい。

    result = {}
    
    tabhandle = newtab_and_switch()
    g.driver.get(url)

    curr_url_form = find_whether_url_formset(url)
    if curr_url_form != -1:
        for j in g.formlist[curr_url_form][1:]:
            print(f"selenium: searching xpath_ {j}")
            element = g.driver.find_element(by=By.XPATH, value=j[0])
            
            if j[1]==0 or j[1]==4: #テキスト入力
                element.send_keys(j[2])
            elif ( j[1]==1 or j[1]==2) and j[2]: #クリック
                element.click()
            elif j[1]==3: #ドロップダウン
                Select(element).select_by_index(j[2])
            elif  j[1]==5 : #クリック
                element.click()
        time.sleep(0.5)
        
        #wordcountを実行
        result["word"] = wordcount( g.driver.page_source )
        
        
        result["status"] = "success"
    else:
        result["status"] = "formdata not found"
    result["tabhandle"] = tabhandle
    result["cookie"] = g.driver.get_cookies()
    result["url"] = g.driver.current_url

    return result


### tag_count ####################################################################################################

def open_taglist():
    st.header("tags to count")
    tagsinput = st.text_area("tags_to_count", label_visibility="collapsed", value="meta, input, form")
    g.tags_to_count = list(dict.fromkeys( re.split(r"[,;| \n、。　・]+", tagsinput) ))
    if "" in g.tags_to_count: g.tags_to_count.remove("")
    
    col0,col1 = st.columns([15,1])
    col0.text(f"total: {len(g.tags_to_count)} {g.tags_to_count}")
    col1.button(":question:", help="入力はカンマ、スペース、改行のいずれかで区切ってください")

def tagCounterchisenon(soup):
        # レスポンスが帰ってきたら
            
        tag_counts = {}
            
        for tag_name in g.tags_to_count:
            tag_counts[tag_name] = {'count': 0, 'line_numbers': []}
            
        tags = soup.find_all(g.tags_to_count)
            
            # 各指定されたタグをカウントおよび行番号を取得
        for tag in tags:
                tag_name = tag.name
                tag_counts[tag_name]['count'] += 1
                tag_counts[tag_name]['line_numbers'].append(tag.sourceline)
            
            # 結果を出力
        #for tag_name, data in tag_counts.items():
        #        print(f'{tag_name}: {data["count"]} 個')
        #        print(f'行番号: {data["line_numbers"]}')
                # returnで返すように変える
                # jsonがいい？形式については後程考える
        
        return tag_counts
    
### csv ####################################################################################################
    
def csvoutput(csv_filepath=None, key=None): #key指定するとそのページのみ出力、指定しないと全ページ出力
    st.session_state["csvOutPutToggle"] = True
    
    #名前、場所の設定
    if csv_filepath == None:
        csv_filepath = os.path.join( g.output_path, 'tags_words_founds.csv')
    elif os.path.isabs(csv_filepath) == False:
        csv_filepath = os.path.join( g.output_path, csv_filepath, 'tags_words_founds.csv') #入力：ids/0

    #CSVファイルの入力
    with open(csv_filepath, 'w', newline='') as csv_file:
        fieldnames = [
            "id",
            "url",
            "tag_name",
            "tag_count",
            "tag_line_numbers",
            "word",
            "word_count"
        ]
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader() #入力するデータの順番を指定？
        
        #ネストdef
        def csv_writerow(key):
            page = st.session_state["pages_tag_data"][key]
            pageword = st.session_state["pages_word_data"][key]
            
            id=page["id"]
            url=page["url"]
            tag_counts=page["data"]
            
            for name in tag_counts:
                row_data = {"id":id, 
                            "url":url, 
                            "tag_name":name, 
                            "tag_count":tag_counts[name]["count"], 
                            "tag_line_numbers":tag_counts[name]["line_numbers"],
                            "word":"", 
                            "word_count":""
                            }
                try:
                    csv_writer.writerow(row_data)
                except Exception as e:
                    print(f"!!!error : csv (tag)output failed : {e}\n")
            
            if pageword != 0:
                for word in pageword: # {ww:1, ff:4}
                    row_data = {"id":id, 
                                "url":url, 
                                "tag_name":"", 
                                "tag_count":"", 
                                "tag_line_numbers":"",
                                "word":word, 
                                "word_count":pageword[word]
                                }
                    try:
                        csv_writer.writerow(row_data)
                    except Exception as e:
                        print(f"!!!error : csv (word)output failed : {e}\n")
                    
        
        if key==None:
            for pageid in st.session_state["pages_tag_data"]:
                csv_writerow(pageid)
        else:
            csv_writerow(key)
        
            
    print(f"tag csv output: {csv_filepath}")
    if key==None:
        st.session_state["csvoutput"] = "done"
        
### certain_word_pickup ########################################################################################

def open_wordfinder():
    st.header("certain_word_finder")
    st.caption("正規表現を用いて、特定の文字列を検索することができます。")
    st.caption("複数指定したい際も、|(パイプ)で区切ってください。")
    g.wordfinder = st.text_input("wordfinder", label_visibility="collapsed", value=r"MBSD{\w+}")
    
def wordcount(text):
    # 正規表現でマッチした文字列を、その個数と共に辞書型で返す 
    wordlist = list(re.findall( g.wordfinder, text) )
    if len(wordlist) == 0: return 0
    
    result = {word: wordlist.count(word) for word in wordlist}
    return result
