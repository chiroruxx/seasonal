package com.chihiro.seasonal.acceptance

import androidx.compose.foundation.clickable
import androidx.compose.foundation.text.BasicText
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** Exercises the UI test harness, without defining application behavior. */
@RunWith(AndroidJUnit4::class)
class AcceptanceInfrastructureTest {
    @get:Rule val compose = createComposeRule()

    @Test
    fun rendersAndUpdatesComposeContent() {
        compose.setContent {
            var clicked by remember { mutableStateOf(false) }
            BasicText(
                if (clicked) "操作を確認" else "テスト用ボタン",
                Modifier.clickable { clicked = true },
            )
        }
        compose.onNodeWithText("テスト用ボタン").assertIsDisplayed().performClick()
        compose.onNodeWithText("操作を確認").assertIsDisplayed()
    }
}
