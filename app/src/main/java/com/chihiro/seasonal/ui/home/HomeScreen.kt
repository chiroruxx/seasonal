package com.chihiro.seasonal.ui.home

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.chihiro.seasonal.ui.designsystem.brand.SeasonalAppName
import com.chihiro.seasonal.ui.designsystem.theme.SeasonalTheme

@Composable
fun HomeScreen(state: HomeUiState, onRetry: () -> Unit) {
    SeasonalTheme {
        Column(
            modifier =
                Modifier.fillMaxSize()
                    .background(MaterialTheme.colorScheme.surface)
                    .padding(WindowInsets.safeDrawing.asPaddingValues())
                    .padding(horizontal = 20.dp, vertical = 16.dp),
        ) {
            SeasonalAppName(modifier = Modifier.fillMaxWidth())
            Box(
                modifier = Modifier.fillMaxSize().padding(top = 28.dp),
                contentAlignment = Alignment.TopCenter,
            ) {
                when (state) {
                    HomeUiState.Loading -> LoadingContent()
                    HomeUiState.Empty -> EmptyContent()
                    is HomeUiState.Content -> FoodContent(state)
                    HomeUiState.Error -> ErrorContent(onRetry)
                }
            }
        }
    }
}

@Composable
private fun LoadingContent() {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        CircularProgressIndicator()
        Text(
            text = "よみこんでいます",
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.padding(top = 16.dp),
        )
    }
}

@Composable
private fun EmptyContent() {
    Text(
        text = "いまは ひょうじできる たべものが ありません",
        style = MaterialTheme.typography.bodyLarge,
        textAlign = TextAlign.Center,
        modifier = Modifier.fillMaxWidth().padding(top = 32.dp),
    )
}

@Composable
private fun FoodContent(state: HomeUiState.Content) {
    LazyColumn(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        items(state.foods, key = { it.id }) { food ->
            Text(food.name, style = MaterialTheme.typography.titleMedium)
        }
    }
}

@Composable
private fun ErrorContent(onRetry: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = "よみこめませんでした",
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center,
        )
        Button(onClick = onRetry, modifier = Modifier.padding(top = 16.dp)) {
            Text("もういちど")
        }
    }
}
