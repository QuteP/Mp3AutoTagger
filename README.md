# Mp3自動打標籤程式

能自動從itunes、spotify、soundcloud、網易雲音樂等網站上抓取音樂信息（含專輯名稱、曲目名稱、曲目編號、專輯封面、發行年份、創作者）並寫入離線音檔中，準確率約在80％上下。這些寫入的信息（標籤）能順利被各大離線音樂播放器讀取。

### 使用前需：

下載相對應的chromedriver

### 執行方式：

進入cmd，移到此py檔的目錄下，打上

```
python  mp3AutoTagger.py
```

後按enter

### 注意事項：

1. 電腦裡應安裝好python和相應的庫。其中selenium需安裝4.2以前的版本（如4.1.x）否則無法執行。


2. 所有音檔皆須按照指定格式命名：

   創作者名稱　-　曲目名稱.mp3

   否則失敗率會大幅上升（也有可能仍會抓到）。

