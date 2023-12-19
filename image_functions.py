import urllib.error, urllib.request
from urllib.parse import urlparse,urljoin
#import numpy as np
#from easyocr import Reader
#from PIL import Image
import os

dst_dir = os.path.join( os.path.join( os.path.dirname( os.path.abspath(__file__) ), 'crawlresult') , 'img' )

#----------------------------------------------------------------------------#
#OCR 文字認識/////////////////////////////////////////////////////////////////#
#----------------------------------------------------------------------------#
if False: #要するにナシ
    # OCRを実行する関数
    def perform_ocr(image_path, target_string):
        reader = Reader(['en'])
        img_pil = Image.open(image_path)
        img_np = np.array(img_pil)
        result = reader.readtext(img_np)
        
        for detection in result:
            recognized_text = detection[1]

            if target_string in recognized_text:
                print(f'Text in image: {recognized_text}')
                print(f'Target string "{target_string}" found in image: {image_path}')
                return  # 検索対象が見つかった場合はここで終了

    # 画像フォルダ内の画像全てにOCRを実行する関数
    def ocr_all_images_in_folder(target_string):
        folder_path = dst_dir
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp'] 
        for file_name in os.listdir(folder_path):
            if any(file_name.lower().endswith(ext) for ext in image_extensions):
                image_path = os.path.join(folder_path, file_name)
                print(f'Performing OCR on: {image_path}')
                perform_ocr(image_path, target_string)


    # 検索対象の文字列
    target_string = 'MBSD{'

    # メイン関数で実行
    #ocr_all_images_in_folder(folder_path, target_string)


#----------------------------------------------------------------------------#
#image download//////////////////////////////////////////////////////////////#
#----------------------------------------------------------------------------#

#画像を保存################################


# 画像を保存するディレクトリを作成
os.makedirs(dst_dir, exist_ok=True)

def download_image(img_url,id=""):
    try:
        #ファイル名はURLの末尾から取得。id_ファイル名 という形式で保存
        filename = f'{id}_{ urlparse(img_url).path.split("/")[-1] }'
        urllib.request.urlretrieve(img_url, os.path.join(dst_dir,filename))
        print(f"saved image as {filename}")
    except Exception as e:
        print(e)

#htmlから画像リンクを取得→保存################################

def getimages(soup, url, id):
    # 画像リンクのリストを取得
    img_list = soup.find_all("img")
    for img in img_list:
        # 画像のURLを取得
        img_url = img.get("src")
        img_url = urljoin(url, img_url)
        # 画像を保存
        download_image(img_url,id)