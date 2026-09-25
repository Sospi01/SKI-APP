package com.sospedra.skiinfo;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.ProgressBar;

import androidx.activity.OnBackPressedCallback;
import androidx.appcompat.app.AppCompatActivity;
import androidx.browser.customtabs.CustomTabsClient;
import androidx.browser.customtabs.CustomTabsIntent;

/**
 * The whole app is this one screen: a WebView pointed at the live Ski Info
 * PWA. There's no offline bundle and no native screens -- the site itself
 * already handles navigation, search and the map; this just gives it an
 * app icon, a launcher entry and no browser chrome.
 */
public class MainActivity extends AppCompatActivity {

    private static final String APP_URL = "https://sospi01.github.io/SKI-APP/";
    private static final Uri APP_URI = Uri.parse(APP_URL);
    private static final String APP_PATH = "/SKI-APP";

    private WebView webView;
    private ProgressBar progressBar;
    private View errorView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webview);
        progressBar = findViewById(R.id.progress);
        errorView = findViewById(R.id.error_view);
        Button retryButton = findViewById(R.id.retry_button);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                if (!request.isForMainFrame()) return false;
                Uri uri = request.getUrl();
                if (isAppPage(uri)) return false;
                openExternally(uri);
                return true;
            }

            @Override
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                progressBar.setVisibility(View.VISIBLE);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                progressBar.setVisibility(View.GONE);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    showError();
                }
            }
        });

        retryButton.setOnClickListener(v -> {
            errorView.setVisibility(View.GONE);
            webView.setVisibility(View.VISIBLE);
            webView.loadUrl(APP_URL);
        });

        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (webView.canGoBack()) {
                    webView.goBack();
                } else {
                    setEnabled(false);
                    getOnBackPressedDispatcher().onBackPressed();
                }
            }
        });

        if (savedInstanceState != null) {
            webView.restoreState(savedInstanceState);
        } else {
            webView.loadUrl(APP_URL);
        }
    }

    private static boolean isAppPage(Uri uri) {
        String path = uri.getPath();
        return "https".equals(uri.getScheme())
                && APP_URI.getHost().equalsIgnoreCase(uri.getHost())
                && path != null
                && (path.equals(APP_PATH) || path.startsWith(APP_PATH + "/"));
    }

    /**
     * Anything outside the app itself (official resort sites, Booking, ...)
     * opens in the system browser via a Custom Tab rather than inside this
     * WebView, which has no address bar and would trap the user there.
     * Pinning the tab to the browser package (instead of letting Android
     * hand the link to, say, the Booking app) keeps affiliate referrals in
     * the same browser session they need to be attributed.
     */
    private void openExternally(Uri uri) {
        String scheme = uri.getScheme();
        boolean isWeb = "http".equals(scheme) || "https".equals(scheme);
        try {
            if (isWeb) {
                String browserPackage = CustomTabsClient.getPackageName(this, null);
                if (browserPackage != null) {
                    CustomTabsIntent tab = new CustomTabsIntent.Builder().setShowTitle(true).build();
                    tab.intent.setPackage(browserPackage);
                    tab.launchUrl(this, uri);
                    return;
                }
            }
            startActivity(new Intent(Intent.ACTION_VIEW, uri));
        } catch (ActivityNotFoundException ignored) {
            // No app can handle this link (e.g. an unusual scheme); nothing to do.
        }
    }

    private void showError() {
        progressBar.setVisibility(View.GONE);
        webView.setVisibility(View.GONE);
        errorView.setVisibility(View.VISIBLE);
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        webView.saveState(outState);
    }
}
