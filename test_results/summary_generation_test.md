# Article Summary Generation Test Results

## Original Article Content

### Full Text
```
First paragraph of the article content.
Second paragraph with technical details.
Third paragraph explaining implementation.
Fourth paragraph with results.
Fifth paragraph with conclusion.
```

### Meta Description
```
This is a meta description of the article.
```

## Grok API Input

### System Instruction
```

        あなたは技術ブログの記事の要約を行うアシスタントです。
        与えられた記事を分析し、簡潔で情報量の多い要約を作成してください。
        技術的な内容は正確に、一般的な内容は分かりやすく要約してください。
        回答は必ず日本語で行ってください。専門用語は適切に翻訳し、必要に応じて英語の専門用語を括弧内に残してください。
        
```

### Complete Prompt
```

        以下の技術ブログの記事を要約してください。

        タイトル: Test Article
        本文: First paragraph of the article content.
Second paragraph with technical details.
Third paragraph explaining implementation.
Fourth paragraph with results.
Fifth paragraph with conclusion.
        
        要約は以下の形式で行い、日本語で回答してください:
        1. 記事の主な内容（1-2文）
        2. 重要なポイント（箇条書き3-5点）
        3. 技術的な洞察
        
```

## Generated Summary
```
Generated summary of the article
```

## Prompt Analysis

### Text Length
Original text length: 187 characters
Text sent to Grok: 187 characters (first 2000 chars)

### Prompt Structure
- 以下の技術ブログの記事を要約してください。
- タイトル: Test Article
- 本文: First paragraph of the article content.
- Second paragraph with technical details.
- Third paragraph explaining implementation.
- Fourth paragraph with results.
- Fifth paragraph with conclusion.
- 要約は以下の形式で行い、日本語で回答してください:
- 1. 記事の主な内容（1-2文）
- 2. 重要なポイント（箇条書き3-5点）
- 3. 技術的な洞察
