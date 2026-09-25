plugins {
    id("com.android.application")
    id("com.google.gms.google-services")
}

android {
    namespace = "com.sospedra.skiinfo"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.sospedra.skiinfo"
        minSdk = 24
        targetSdk = 36
        versionCode = 5
        versionName = "1.0.3"
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
    implementation("androidx.browser:browser:1.8.0")
    implementation(platform("com.google.firebase:firebase-bom:33.5.1"))
    implementation("com.google.firebase:firebase-analytics")
}

// androidx.activity and androidx.appcompat pull in different, incompatible
// versions of the Kotlin stdlib split artifacts transitively (this app has
// no Kotlin code of its own). Forcing one consistent version avoids
// checkReleaseDuplicateClasses failing on classes that exist in both
// kotlin-stdlib and the older separate kotlin-stdlib-jdk7/jdk8 jars.
configurations.all {
    resolutionStrategy {
        force("org.jetbrains.kotlin:kotlin-stdlib:1.9.24")
        force("org.jetbrains.kotlin:kotlin-stdlib-jdk7:1.9.24")
        force("org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.24")
    }
}
