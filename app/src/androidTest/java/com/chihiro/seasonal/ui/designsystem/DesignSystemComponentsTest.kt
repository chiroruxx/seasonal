package com.chihiro.seasonal.ui.designsystem

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.painter.ColorPainter
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performSemanticsAction
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.dp
import com.chihiro.seasonal.ui.designsystem.common.FoodCard
import com.chihiro.seasonal.ui.designsystem.common.SeasonalModalBottomSheet
import com.chihiro.seasonal.ui.designsystem.theme.SeasonalTheme
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

class DesignSystemComponentsTest {
    @get:Rule val composeRule = createComposeRule()

    @Test
    fun selectingFoodCardShowsDetailSheetAndCloseDismissesIt() {
        composeRule.setContent { FoodCardWithDetail() }

        composeRule.onNodeWithText("だいこん").performClick()
        composeRule.onNodeWithText("えらびかた").assertIsDisplayed()
        composeRule.onNodeWithContentDescription("とじる").performClick()
        composeRule.onNodeWithText("えらびかた").assertDoesNotExist()
    }

    @Test
    fun foodNameRemainsPresentAtLargeFontScale() {
        val name = "ながくてよみにくくならないだいこんのなまえ"
        composeRule.setContent {
            val density = LocalDensity.current
            CompositionLocalProvider(
                LocalDensity provides Density(density.density, fontScale = 2f),
            ) {
                SeasonalTheme {
                    FoodCard(
                        name = name,
                        illustration = ColorPainter(Color(0xFFFFDDB8)),
                        contentDescription = "だいこんの全体",
                        onClick = {},
                        modifier = Modifier.width(112.dp),
                    )
                }
            }
        }

        val textLayoutResults = mutableListOf<TextLayoutResult>()
        composeRule
            .onNodeWithText(name, useUnmergedTree = true)
            .assertIsDisplayed()
            .performSemanticsAction(SemanticsActions.GetTextLayoutResult) { getResults ->
                assertTrue(getResults(textLayoutResults))
            }

        assertEquals(1, textLayoutResults.size)
        val textLayout = textLayoutResults.single()
        assertFalse(textLayout.hasVisualOverflow)
        assertTrue(textLayout.lineCount > 1)
        assertEquals(
            name.length,
            textLayout.getLineEnd(textLayout.lineCount - 1, visibleEnd = true),
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun FoodCardWithDetail() {
    var selected by remember { mutableStateOf(false) }
    SeasonalTheme {
        Column(modifier = Modifier.height(700.dp)) {
            FoodCard(
                name = "だいこん",
                illustration = ColorPainter(Color(0xFFFFDDB8)),
                contentDescription = "だいこんの全体",
                onClick = { selected = true },
            )
        }
        if (selected) {
            SeasonalModalBottomSheet(title = "だいこん", onDismissRequest = { selected = false }) {
                androidx.compose.material3.Text("えらびかた")
            }
        }
    }
}
