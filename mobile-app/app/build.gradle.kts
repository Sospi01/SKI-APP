plugins {
    id("com.android.application")
}

android {
    namespace = "com.sospedra.skiinfo"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.sospedra.skiinfo"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
    }

    val keystorePath = System.getenv("SKIINFO_KEYSTORE_PATH")
    val hasSigningConfig = !keystorePath.isNullOrEmpty()

    signingConfigs {
        if (hasSigningConfig) {
            create("release") {
                storeFile = file(keystorePath!!)
                storePassword = System.getenv("SKIINFO_KEYSTORE_PASSWORD")
                keyAlias = System.getenv("SKIINFO_KEY_ALIAS")
                keyPassword = System.getenv("SKIINFO_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            if (hasSigningConfig) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.activity:activity:1.9.1")
}
