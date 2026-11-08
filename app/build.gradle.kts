import javax.xml.parsers.DocumentBuilderFactory

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.compose.compiler)
}

val distributionBuild =
    providers.gradleProperty("distributionBuild").orElse("false").get().toBooleanStrict()
val distributionVersionCode = providers.gradleProperty("distributionVersionCode").orNull

if (distributionBuild) {
    require(distributionVersionCode?.toIntOrNull() in 2..2_100_000_000) {
        "A distribution build requires distributionVersionCode between 2 and 2100000000"
    }
}

android {
    namespace = "com.chihiro.seasonal"
    compileSdk {
        version =
            release(36) {
                minorApiLevel = 1
            }
    }

    defaultConfig {
        applicationId = "com.chihiro.seasonal"
        minSdk = 36
        targetSdk = 36
        versionCode = if (distributionBuild) distributionVersionCode!!.toInt() else 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        if (
            !providers
                .gradleProperty("includePendingAcceptance")
                .orElse("false")
                .get()
                .toBooleanStrict()
        ) {
            testInstrumentationRunnerArguments["notAnnotation"] =
                "com.chihiro.seasonal.acceptance.PendingAcceptance"
        }
        providers.gradleProperty("acceptanceTestClass").orNull?.let {
            require(it.isNotBlank()) { "acceptanceTestClass must not be blank" }
            testInstrumentationRunnerArguments["class"] = it
        }
    }

    buildFeatures { compose = true }

    testOptions {
        animationsDisabled = true
        managedDevices {
            localDevices {
                create("pixel2Api36") {
                    device = "Pixel 2"
                    apiLevel = 36
                    systemImageSource = "aosp-atd"
                }
            }
        }
    }

    buildTypes {
        if (distributionBuild) {
            val signingValues =
                listOf(
                        "SEASONAL_DEBUG_KEYSTORE_PATH",
                        "SEASONAL_DEBUG_STORE_PASSWORD",
                        "SEASONAL_DEBUG_KEY_ALIAS",
                        "SEASONAL_DEBUG_KEY_PASSWORD",
                    )
                    .associateWith { name ->
                        providers.environmentVariable(name).orNull?.takeIf { it.isNotBlank() }
                            ?: error("A distribution build requires $name")
                    }
            val distributionSigning =
                signingConfigs.create("distributionDebug") {
                    storeFile = file(signingValues.getValue("SEASONAL_DEBUG_KEYSTORE_PATH"))
                    storePassword = signingValues.getValue("SEASONAL_DEBUG_STORE_PASSWORD")
                    keyAlias = signingValues.getValue("SEASONAL_DEBUG_KEY_ALIAS")
                    keyPassword = signingValues.getValue("SEASONAL_DEBUG_KEY_PASSWORD")
                }
            getByName("debug") { signingConfig = distributionSigning }
        }
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.viewmodel)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.kotlinx.coroutines.android)
    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.compose.foundation)
    debugImplementation(libs.androidx.compose.ui.test.manifest)
    debugImplementation(libs.androidx.compose.ui.tooling)
}

// Verify the actual managed-device report, including explicit selections that match no tests.
tasks.register("acceptanceTest") {
    group = "verification"
    description = "Run API 36 Compose acceptance tests and require a nonempty passing result."
    dependsOn("pixel2Api36DebugAndroidTest")
    doLast {
        val results =
            fileTree(layout.buildDirectory.dir("outputs/androidTest-results/managedDevice/debug")) {
                include("**/TEST-*.xml")
            }
        check(!results.isEmpty) { "No managed-device test results were produced" }
        val factory =
            DocumentBuilderFactory.newInstance().apply {
                setFeature("http://apache.org/xml/features/disallow-doctype-decl", true)
            }
        var count = 0
        results.files.forEach { report ->
            val document = factory.newDocumentBuilder().parse(report)
            count += document.getElementsByTagName("testcase").length
            check(
                document.getElementsByTagName("failure").length == 0 &&
                    document.getElementsByTagName("error").length == 0 &&
                    document.getElementsByTagName("skipped").length == 0,
            ) {
                "Acceptance tests failed or were skipped: $report"
            }
        }
        check(count > 0) { "No acceptance tests executed; inspect the test selection" }
        logger.lifecycle("Verified $count acceptance test(s)")
    }
}
