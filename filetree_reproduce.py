# 出力したjsonをもとに、ファイル構造を再現(reproduce)。

import os, json, shutil, glob
import global_value as g
import streamlit as st
from urllib.parse import urlparse, urljoin
from collections import deque
from win32com.client import Dispatch
import shutil

# ページ毎にフォルダで表し、その中に「page.html」、「suspend.csv」、「request-result.txt」やらぶっこむ形。
# URL上の階層構造はフォルダのツリー構造に書き起こせそう。
# 外部リンク(farChild)とか入っていたら、そのページに飛ぶ'ショートカット'を生成する感じ。

# crawlerフォルダでターミナルを起動し、そこで本ファイルとクローラを起動した際のファイルパス↓
output_path = os.path.join( os.path.dirname( os.path.abspath(__file__) ), 'crawlresult')
filepath_json = os.path.join(output_path,'crawled_pages.json')
filepath_table= os.path.join(output_path,'id_url_linktable.json')

reproroot_path = os.path.join( output_path, 'reproduced')
 
all_page = json.load( open(filepath_json, "r", encoding="utf-8"))
table= json.load( open(filepath_table,"r",encoding="utf-8"))
pathdict = {} #idをキーとして、そのidのページのosパスを格納する辞書


# https://docs.python.org/ja/3/library/urllib.parse.html
def get_url_lastname(id):
    url = table["geturl"][id]
    url_path = ( urlparse(url)[1] + urlparse(url)[2] ).split("/")
    
    # 最後の要素を取得 ''がsplit後の最後の値と見なされてしまってはまずいので、そのひとつ前を選択
    url_path = url_path[-1 -(url_path[-1]=='')]
    # 例 ['', '32', '']
    # 　 ['', '42', '42-011.php']
    
    return url_path

# idsに保存した各情報をコピー
def copy_from_ids(id,gen_path):
    id_path = os.path.join( output_path, "ids", str(id) )
    
    for file in glob.glob( os.path.join(id_path,"*") ):
        shutil.copy(file,gen_path)

# 通常のフォルダ作成
def generate_netloc_path(id):
    url = table["geturl"][id]
    url_path = os.path.join( reproroot_path, urlparse(url)[1] + urlparse(url)[2] ) #指定URLのネットロケーションを生成
    print(f"generate folder_id{id}: "+url_path)
    try:
        os.makedirs( url_path ,exist_ok=True ) #そのネットロケーションのフォルダを作成
        
        copy_from_ids(id,url_path)
        
    except:
        print("!!!error : generate failed")
        return -1
    pathdict[id] = url_path #登録
    return 0

# 生成 ##########################################################

def filetree_reproduce():

    # 見つけたdirChildを順に格納するキュー
    dirqueue = deque()
    nofargen = set()
    if "root" in table["parents"]:
        dirqueue.append( table["parents"]["root"] )
    else:
        dirqueue.append( 0 )
    #rootディレクトリを作成
    os.makedirs( reproroot_path ,exist_ok=True )


    while len(dirqueue) > 0:
        current_id = dirqueue.popleft()
        url = table['geturl'][current_id]
        currentpath = os.path.join( reproroot_path , urlparse(url)[1] + urlparse(url)[2] )
        print(f"currentpath:{currentpath}")
        
        for child in all_page[str(current_id)]["dirChild"]:
            #childはdirChild_id
            g.output_state.error(f"step2/3. フォルダ生成中(残り{len(dirqueue)}個)...")
            # 子ディレクトリを作成
            generate_netloc_path(child)
            # その子ディレクトリのidをキューに追加
            dirqueue.append( child )
            
        if len( all_page[str(current_id)]["farChild"] ) > 0:
            #childはfarChild_id
            nofargen.add(current_id)
            ...

    while len(nofargen) > 0:
        
        current_id = nofargen.pop()
        url = table['geturl'][current_id]
        currentpath = os.path.join( reproroot_path , urlparse(url)[1] + urlparse(url)[2] )
        
        for child in all_page[str(current_id)]["farChild"]:
            #childはfarChild_id
            if not (child in pathdict) : 
                if generate_netloc_path(child) == -1:
                    continue
            g.output_state.error(f"step3/3. 外フォルダショートカット生成中(残り{len(nofargen)}個)...")
            #ショートカットを作成
            shortcutpathname = os.path.join( currentpath , get_url_lastname(child) ) + ".lnk"
            
            print(f"generate shortcut: {shortcutpathname} -> {table['geturl'][child]}") 
            try:
                shortcut = Dispatch("WScript.Shell").CreateShortCut(shortcutpathname)
            except Exception as e:
                print("!!!error : generate failed: ",e)
                continue
            shortcut.Targetpath  = os.path.abspath(pathdict[child])
            try:
                shortcut.save()
            except Exception as e:
                print("!!!error : generate failed: ",e)
                continue
