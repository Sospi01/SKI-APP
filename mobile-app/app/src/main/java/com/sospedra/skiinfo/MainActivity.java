package com.sospedra.skiinfo;

import android.Manifest;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.ProgressBar;

import androidx.activity.OnBackPressedCallback;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.browser.customtabs.CustomTabsClient;
import androidx.browser.customtabs.CustomTabsIntent;
import androidx.core.content.ContextCompat;

import java.util.Locale;

/**
 * The whole app is this one screen: a WebView pointed at the live Ski Info
 * PWA. There's no offline bundle and no native screens -- the site itself
 * already handles navigation, search and the map; this just gives it an
 * app icon, a launcher entry and no browser chrome.
 */
public class MainActivity extends AppCompatActivity {

    private static final String APP_URL = "https://skiinfoapp.com/";
    // The site's old GitHub Pages address now redirects to APP_URL; still
    // treat it as the app's own page in case a link or redirect points there.
    private static final String LEGACY_HOST = "sospi01.github.io";
    private static final String LEGACY_PATH = "/SKI-APP";

    private WebView webView;
    private ProgressBar progressBar;
    private View errorView;

    // The site asks for the location ("where am I" on the piste map, nearby
    // resorts) through the browser API; the WebView hands that request here,
    // and Android's own permission prompt answers it. Nothing is stored or
    // sent by the app: the position only ever goes to the page on screen.
    private GeolocationPermissions.Callback pendingGeoCallback;
    private String pendingGeoOrigin;
    private final ActivityResultLauncher<String[]> locationPermissionLauncher =
            registerForActivityResult(new ActivityResultContracts.RequestMultiplePermissions(), result -> {
                boolean granted = Boolean.TRUE.equals(result.get(Manifest.permission.ACCESS_FINE_LOCATION))
                        || Boolean.TRUE.equals(result.get(Manifest.permission.ACCESS_COARSE_LOCATION));
                if (pendingGeoCallback != null) pendingGeoCallback.invoke(pendingGeoOrigin, granted, false);
                pendingGeoCallback = null;
                pendingGeoOrigin = null;
            });

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
        settings.setGeolocationEnabled(true);
        // Lets the site's "Compartir" button open Android's share sheet
        // (docs/station-actions.js looks for window.SkiInfoAndroid). Only the
        // app's own pages ever load here; everything else opens externally.
        webView.addJavascriptInterface(new ShareBridge(), "SkiInfoAndroid");

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                if (origin == null || !isAppPage(Uri.parse(origin))) {
                    callback.invoke(origin, false, false);
                    return;
                }
                if (hasLocationPermission()) {
                    callback.invoke(origin, true, false);
                    return;
                }
                pendingGeoOrigin = origin;
                pendingGeoCallback = callback;
                locationPermissionLauncher.launch(new String[] {
                        Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION });
            }
        });

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
            webView.loadUrl(startUrl());
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
            webView.loadUrl(startUrl());
        }
    }

    /**
     * The home page in the phone's language: the Spanish home sends
     * ?applang=xx on to /xx/ unless the person already picked a language on
     * the site (docs/index.html, lang-redirect). Spanish and the other
     * languages of Spain stay on the Spanish home; anything else not
     * available gets English.
     */
    private static String startUrl() {
        String lang = Locale.getDefault().getLanguage();
        switch (lang) {
            case "es": case "ca": case "eu": case "gl": return APP_URL;
            case "fr": case "de": case "it": return APP_URL + "?applang=" + lang;
            default: return APP_URL + "?applang=en";
        }
    }

    private boolean hasLocationPermission() {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    private class ShareBridge {
        // Tells the site this app version answers location requests (1.0.6+),
        // so it shows its "where am I" and "use my location" buttons here too.
        @JavascriptInterface
        public boolean hasLocation() {
            return true;
        }

        @JavascriptInterface
        public void share(String text, String url) {
            if (url == null || !url.startsWith("https://")) return;
            Intent send = new Intent(Intent.ACTION_SEND);
            send.setType("text/plain");
            send.putExtra(Intent.EXTRA_TEXT, (text == null || text.isEmpty() ? "" : text + "\n") + url);
            runOnUiThread(() -> {
                try {
                    startActivity(Intent.createChooser(send, "Compartir"));
                } catch (ActivityNotFoundException ignored) {
                    // No app can share text: nothing sensible to do.
                }
            });
        }
    }

    private static boolean isAppPage(Uri uri) {
        String host = uri.getHost();
        String path = uri.getPath();
        if (!"https".equals(uri.getScheme()) || host == null) return false;
        if (host.equalsIgnoreCase("skiinfoapp.com") || host.equalsIgnoreCase("www.skiinfoapp.com")) return true;
        return host.equalsIgnoreCase(LEGACY_HOST)
                && path != null
                && (path.equals(LEGACY_PATH) || path.startsWith(LEGACY_PATH + "/"));
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
