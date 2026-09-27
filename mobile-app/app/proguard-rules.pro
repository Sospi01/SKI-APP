# The WebView calls the share bridge by name (MainActivity.ShareBridge).
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
