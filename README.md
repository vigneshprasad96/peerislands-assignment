# Java Codebase Knowledge Extractor

LLM-powered tool for analyzing Java codebases and extracting structured knowledge with semantic search capabilities.

## Quick Start

```bash
# Install dependencies
poetry install

# Configure
cp .env
# Edit .env with your GROQ_API_KEY, REPO_URL, and GIT_TOKEN

# Run
poetry run python main.py
```

## Output

- `structured_knowledge.json` - Comprehensive JSON with project overview, class summaries, method signatures, and complexity metrics
- `chroma_store/` - Vector database for semantic search
- `knowledge_extraction.log` - Execution logs

---

## Best Practices Implemented

### 1. **Modular Architecture**
- Separation of concerns: Each module has single responsibility
- Independent, testable components
- Clear dependency hierarchy
- Easy to extend with new parsers or LLM providers

### 2. **Token Management**
- Conservative chunking (3500 tokens) to prevent API errors
- Overlap (300 tokens) to maintain context
- Smart splitting on code structure boundaries (class/method declarations)
- Sequential processing to avoid rate limits

### 3. **Error Handling & Resilience**
- Retry logic for LLM calls (3 attempts with exponential backoff)
- Graceful handling of parse errors (malformed Java syntax)
- Token masking in logs for security
- Comprehensive exception handling at all levels
- Informative error messages with remediation steps

### 4. **Authentication & Rate Limiting**
- Git Personal Access Token support for GitHub rate limits
- Automatic token injection into clone URLs
- Environment-based configuration (never hardcoded secrets)
- Rate limit awareness (60 requests/hour → 5000 with token)

### 5. **Code Quality**
- Type hints throughout for clarity
- Centralized configuration management
- Professional logging (file + console)
- UTF-8 encoding support for international codebases
- JSON serialization safety (sets → lists)

### 6. **Data Integrity**
- AST-based parsing (accurate structure extraction)
- Cyclomatic complexity calculation for all methods
- Package and import tracking
- Relationship mapping (inheritance, interfaces)

### 7. **Performance Optimization**
- Incremental file processing (no full memory load)
- Efficient JSON serialization
- Vector database for fast semantic search
- Reuses existing cloned repositories

---

## Assumptions

### Technical Assumptions
1. **Java Version**: Compatible with Java 8+ syntax (javalang parser limitation)
2. **File Encoding**: All source files are UTF-8 encoded
3. **Repository Structure**: Standard Maven/Gradle project layout
4. **Network Access**: Stable internet for API calls and Git operations
5. **Python Version**: Python 3.8+ required (type hints, f-strings)

### LLM Assumptions
1. **Model Availability**: Groq API with LLaMA 3.3 70B accessible
2. **Token Limits**: Single class/method fits within chunk size (3500 tokens)
3. **Response Quality**: LLM provides structured, consistent summaries
4. **Cost**: API usage incurs costs (~$0.59/million tokens for LLaMA 3.3)

### Repository Assumptions
1. **Access**: Public repositories or authenticated access via PAT
2. **Size**: Repository cloneable within reasonable time/space
3. **Validity**: Repository contains parseable Java code
4. **Git Protocol**: HTTPS or SSH protocols supported

---

## Limitations

### 1. **Language Support**
- **Current**: Java only
- **Limitation**: Cannot parse Python, JavaScript, C++, etc.
- **Workaround**: Extend with additional parsers (e.g., `ast` for Python)

### 2. **Code Complexity**
- **Issue**: Very large classes (>10,000 lines) may exceed chunk size
- **Impact**: Partial analysis or errors
- **Mitigation**: Increase `CHUNK_SIZE` or split analysis

### 3. **JavaDoc & Comments**
- **Issue**: Comments are filtered out during parsing
- **Impact**: Misses developer-written documentation
- **Workaround**: Modify `safe_to_dict()` to preserve documentation nodes

### 4. **Performance**
- **Speed**: ~2-5 seconds per class for LLM analysis
- **Large Repos**: 1000+ classes = 30-60 minutes
- **Bottleneck**: Sequential LLM calls (rate limiting)
- **Improvement**: Implement batch processing or parallel requests

### 5. **LLM Accuracy**
- **Issue**: Summaries depend on model interpretation
- **Impact**: May miss nuances or misinterpret complex patterns
- **Example**: Generic summaries for boilerplate code
- **Mitigation**: Use temperature=0 for consistency

### 6. **Storage**
- **In-Memory State**: No persistence between runs
- **Limitation**: Re-analysis required for updates
- **Disk Usage**: Cloned repo + vector DB + JSON (~GB for large repos)

### 7. **Error Recovery**
- **Partial Failures**: If LLM fails for one class, continues processing
- **No Rollback**: Partial results saved even on errors
- **Manual Cleanup**: Failed clones require manual directory removal

### 8. **Security**
- **Token Exposure**: Tokens visible in process environment
- **Log Files**: May contain sensitive repo names/paths
- **Network**: API keys transmitted over network
- **Recommendation**: Use secrets management, rotate tokens regularly

### 9. **Git Operations**
- **Clone Speed**: Large repositories (>1GB) may be slow
- **Submodules**: Not automatically cloned
- **LFS**: Large files not handled efficiently
- **Workaround**: Manual clone with `--depth 1` for shallow clone

---

## Project Structure

```
knowledge-extractor/
├── config.py              # Configuration management
├── logger.py              # Logging setup
├── java_parser.py         # Java AST parsing
├── llm_service.py         # LLM integration
├── git_cloner.py          # Repository cloning
├── repository_scanner.py  # File discovery
├── knowledge_structurer.py # Knowledge organization
├── vector_store.py        # Vector database
├── main.py                # Entry point
├── pyproject.toml         # Dependencies
└── .env                   # Configuration (not in git)
```

---

## License

MIT

## Author

Vignesh Prasad

---

**Version**: 1.0.0  
**Last Updated**: November 2025