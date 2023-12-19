# delikitchup

---
## 動作環境
- **OS**: Windows11
- **Python3**: 最新のものがインストールされているものとします。
- **ブラウザはchromeを使用するものとします**
- **ライブラリ等も記載がなければ2023/11/13時点で最新のものを使用してください**

## 起動説明
1. **Pythonのライブラリインストール**
    
    このツールを使用する際、これらのライブラリをインストールする必要があります。
    - requests
    - beautifulsoup4
    - streamlit
    - selenium
    - pywin32
    - chromedriver-binary-sync
    - chromedriver-binary-auto

    これらのライブラリが導入されていない場合、導入してPCを再起動してください
    chromedriver-bainary-xxxは後述の「download_chromedriver.py」を使用せず、自分でChromedriverをダウンロードする場合不要です。
    ```
    pip install requests beautifulsoup4 streamlit selenium pywin32 chromedriver-binary-sync chromedriver-binary-auto
    ```

2. **Chromedriverのダウンロード**
    
    このプログラムではchromedriverを使用しています。
    下記リンクからご利用のChromeバージョンに対応したChromedriverをダウンロードし、delikitchup.pyのあるファイルに入れてください。
    https://googlechromelabs.github.io/chrome-for-testing/
    
    オンライン環境の場合、「download_chromedriver.py」を実行することで、自動で対応driverをダウンロードできます。


3. **Windowsで受け取ったファイルでコマンドプロンプトを起動**

    start_delikitchup.batを起動することで始めることが出来ます。
    delikitchup.pyのあるディレクトリにcmdで遷移してから下記のように入力することで起動することもできます。
    ```
    streamlit run --server.address localhost "delikitchup.py"
    ```
    また、'steramlit'を認識しない等のエラーで上記のbatファイルで起動できなかった場合、下記のコードで起動してください。
    ```
    python -m streamlit run delikitchup.py
    ```
    streamlit初回起動時にemailを聞かれますが無視して大丈夫です。enterで飛ばせます。

---
## 操作説明

### Main/option

- Scan time span: クローラーが次のページにアクセスするまでの時間を設定します。単位は秒です。
- URL most contains: ここに入力した文字列がURLに含まれているページにのみアクセスします。「 http://example.jp/ 」のように入力すればドメインを指定することも可能です。
- crawlstart URL: ここに入力したURLから探索が始まります。
- limit explore count: 探索するページ数の上限を設定します。マイナス値で無限になり、探索しうる全ページにアクセス後終了します。
- chromedriver path: ここにはChromedriverのPathを指定してください。パス末尾には"\chromedriver" を含めて入力してください。pathはフルパスで書くことを推奨します。右クリックでパスを取得した場合ダブルクォーテーションで囲まれていますが、ダブルクォーテーションはつけずに入力してください。
- output crawl result: クローラーが持ってきたデータを元にcsvを生成します。
- whether save html: ページ毎にHTMLタグ検索を実行し、内部情報を絞って確認できます。
- whether get crawl data: クロール中、各ページのHTMLを複製します。

### per-page settings
- forms auto enter: xpathとその属性を指定してその場所に何を入れたいかを記述します。"add xpath-content"からそのページで自動入力する要素を追加できます。また、"add page URL"で新しく入力したいページを追加します。右のeditとdeleteで編集、削除ができます。
- blacklist: ここに書いたURLにはアクセスしません。URLの区切りは改行で行ってください。
- tags to count: csvで出力するhtmlタグを設定します。入力はカンマ、スペース、改行のいずれかで区切ってください。

このクローラーでは予めクロールするサイトのログイン情報などを保存し、seleniumを使用して自動入力をしています。
入力したいページ、そのページで入力したい情報、そしてそのxpathをクローラー上部の"per-page settings"から行って下さい。
xpathはGoogleChromeなどのブラウザであればF12の開発者ツールなどから確認することができます。
- **xpath**: 入力箇所の位置 
- **type**: 入力箇所の形式
- **content**: 入力する内容
※注意：あらかじめ入力がないformはスキップされます。

### crawl data
- クロールしたデータのページごとの詳細を見ることができます。

## ファイルツリー(サイトマップ)
探索が終わるとファイルツリーが作成されます。
ファイルの中にはそのページのcsvがあります。
探索範囲外(URL most containsに入力されてないURL)のフォルダも生成されますが、それらには中身がありません。

---

## 優位点
### ユーザービリティの高さ
- 進捗のリアルタイム表示
- 簡単なボタン操作
- 取得するタグの変更が容易に可能
- 一度実行しても実行オプションが保存されていて消えることがない
- 起動が簡単でわかりやすい

### サイトマップによる視覚化
- ファイルツリーを生成するので視覚的に分かりやすい
- 他人にサイトマップの説明をするのが容易

### form自動入力
- あらかじめ情報を入力しておくことにより、
  ログインや検索ボックスなどに自動で入力し、次ページ情報の取得が可能。

### クロスドメインへの対応
- URL most contains 設定により探索範囲を指定できる。
  この際、ドメインの一部のみを設定することにより、
  news.example.jpやsearch.example.jpなど、クロスドメインでも探索範囲に含めることが可能

### 設定によってさまざまな用途に使用可能
- htmlの複製やタグ取得をせずにクロールを行うこともできる
- 速度を求める際に余計な機能を簡単に削ることができる
- ページの探索上限を定めることで網羅性の変更が可能

### CSVやJSON出力による作業効率の向上
- csv出力によって脆弱性診断をしなければならない場所の特定が容易

### 負担軽減および高速化
- htmlデータのみ取得しているのでサーバ側の負担が少ない

---
## 注意点
- このツールはformタグやaタグを通してクロールしています。JavaScript等によるリクエスト送信には対応しておりません。
- このツールを他の個人や企業のサイトに対して使用する際は常識の範囲内で行ってください。
- スクレイピングでは、著作権の問題や、サーバー側の負荷、各種サイトの規約やマナーなどを考慮する必要があります。

## ライセンス
このツールはこれらのライブラリ等のライセンスに準拠して作られています
- requests
- beautifulsoup4
- streamlit
- selenium
- chromedriver