package com.chihiro.seasonal.ui.designsystem.brand

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.chihiro.seasonal.R
import com.chihiro.seasonal.ui.designsystem.theme.LightPrimaryContainer
import com.chihiro.seasonal.ui.designsystem.theme.LightSecondary
import com.chihiro.seasonal.ui.designsystem.theme.SeasonalTheme

private val RoundedJapanese = FontFamily(Font(R.font.rounded_mplus_1c_bold))
private val BrandOrange = Color(0xFF9B5424)
private val UnderlineOrange = Color(0xFFDBA565)

@Composable
fun SeasonalAppName(modifier: Modifier = Modifier) {
    Column(modifier = modifier) {
        Text(
            text = "旬なもの",
            color = BrandOrange,
            fontFamily = RoundedJapanese,
            fontWeight = FontWeight.Normal,
            fontSize = 31.sp,
            letterSpacing = 2.sp,
            lineHeight = 44.sp,
        )
        Canvas(
            modifier = Modifier.fillMaxWidth().height(8.dp).padding(horizontal = 2.dp),
        ) {
            val underline =
                Path().apply {
                    moveTo(0f, size.height * 0.26f)
                    cubicTo(
                        size.width * 0.28f,
                        size.height * 1.03f,
                        size.width * 0.70f,
                        size.height * 1.03f,
                        size.width,
                        size.height * 0.26f,
                    )
                }
            drawPath(underline, color = UnderlineOrange, style = Stroke(width = 3.dp.toPx()))
        }
    }
}

@Composable
fun SeasonalLogo(modifier: Modifier = Modifier) {
    Box(
        modifier =
            modifier.size(56.dp).clip(RoundedCornerShape(18.dp)).semantics {
                contentDescription = "旬なもののロゴ"
            },
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.matchParentSize()) {
            drawRoundRect(
                color = LightPrimaryContainer,
                cornerRadius = androidx.compose.ui.geometry.CornerRadius(18.dp.toPx()),
            )
            val leaf =
                Path().apply {
                    moveTo(size.width * 0.68f, size.height * 0.24f)
                    cubicTo(
                        size.width * 0.66f,
                        size.height * 0.08f,
                        size.width * 0.83f,
                        size.height * 0.04f,
                        size.width * 0.91f,
                        size.height * 0.13f,
                    )
                    cubicTo(
                        size.width * 0.89f,
                        size.height * 0.23f,
                        size.width * 0.77f,
                        size.height * 0.29f,
                        size.width * 0.68f,
                        size.height * 0.24f,
                    )
                    close()
                }
            drawPath(leaf, color = LightSecondary)
            val vein =
                Path().apply {
                    moveTo(size.width * 0.69f, size.height * 0.24f)
                    lineTo(size.width * 0.84f, size.height * 0.12f)
                }
            drawPath(vein, color = LightPrimaryContainer, style = Stroke(width = 1.4.dp.toPx()))
        }
        Text(
            text = "旬",
            color = MaterialTheme.colorScheme.primary,
            fontFamily = RoundedJapanese,
            fontSize = 32.sp,
            fontWeight = FontWeight.Normal,
            modifier = Modifier.align(Alignment.Center).padding(top = 5.dp),
        )
    }
}

@Preview(showBackground = true)
@Composable
private fun SeasonalBrandPreview() {
    SeasonalTheme {
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(16.dp)) {
            SeasonalLogo()
            SeasonalAppName(modifier = Modifier.padding(start = 12.dp).width(156.dp))
        }
    }
}
