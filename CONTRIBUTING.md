# Contributing to Camera Analytics

Thank you for your interest in contributing to Camera Analytics! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to Contribute

### 🐛 Report Bugs

Report bugs by [opening an issue](https://github.com/qvidal01/camera-analytics/issues/new). Include:

- Clear, descriptive title
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version, camera type)
- Relevant logs or screenshots

### 💡 Suggest Features

Suggest features by [opening an issue](https://github.com/qvidal01/camera-analytics/issues/new) with:

- Clear use case description
- Why this feature would be useful
- Proposed API or user interface (optional)

### 📝 Improve Documentation

Documentation improvements are always welcome! You can:

- Fix typos or clarify explanations
- Add examples or tutorials
- Improve API documentation
- Translate documentation

### 🔧 Submit Code Changes

See the [Development Setup](#development-setup) section below.

## Good First Issues

Look for issues labeled [`good first issue`](https://github.com/qvidal01/camera-analytics/labels/good%20first%20issue):

- Add support for new camera brands/models
- Implement additional notification channels (Slack, Discord, Telegram)
- Add new object detection classes
- Improve error messages
- Write tests to increase coverage
- Create example scripts or tutorials

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/camera-analytics.git
cd camera-analytics

# Add upstream remote
git remote add upstream https://github.com/qvidal01/camera-analytics.git
```

### 2. Create Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 4. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=camera_analytics --cov-report=html

# Run specific test file
pytest tests/unit/test_detection_engine.py

# Run tests matching a pattern
pytest -k "test_camera"
```

### Code Formatting

We use `black` for formatting and `ruff` for linting:

```bash
# Format code
black src/ tests/

# Check formatting (without modifying)
black --check src/ tests/

# Lint code
ruff check src/ tests/

# Auto-fix linting issues
ruff check src/ tests/ --fix
```

### Type Checking

```bash
# Run mypy
mypy src/ --ignore-missing-imports
```

### Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`:

```bash
# Run manually on all files
pre-commit run --all-files
```

If hooks fail, fix the issues and commit again.

## Code Style Guidelines

### Python Code

- Follow [PEP 8](https://pep8.org/)
- Use type hints for all functions
- Maximum line length: 100 characters
- Use descriptive variable names

```python
# Good
async def detect_objects(
    frame: np.ndarray,
    confidence_threshold: float = 0.5,
) -> List[Detection]:
    """Detect objects in frame."""
    pass

# Bad
def detect(f, c=0.5):
    pass
```

### Documentation

- Add docstrings to all public functions/classes (Google style)
- Include usage examples in docstrings when helpful
- Update README.md if adding user-facing features

```python
def process_frame(frame: np.ndarray, resize: bool = True) -> np.ndarray:
    """
    Process video frame for detection.

    Args:
        frame: Input frame as numpy array (BGR format)
        resize: Whether to resize frame to model input size

    Returns:
        Processed frame ready for inference

    Example:
        >>> frame = cv2.imread("image.jpg")
        >>> processed = process_frame(frame)
    """
    pass
```

### Testing

- Write tests for new functionality
- Maintain or improve code coverage (target: 80%+)
- Use descriptive test names: `test_<what>_<condition>_<expected>`

```python
def test_detection_confidence_threshold_validation():
    """Test that invalid confidence thresholds raise ValueError."""
    with pytest.raises(ValueError):
        DetectionEngine(confidence_threshold=1.5)
```

### Commits

- Use clear, descriptive commit messages
- Follow [Conventional Commits](https://www.conventionalcommits.org/) format
- Reference issues in commit messages

```
feat: add support for Dahua camera authentication
fix: resolve memory leak in frame buffering (fixes #123)
docs: update installation instructions for macOS
test: add integration tests for alert rules
refactor: simplify detection engine initialization
```

## Pull Request Process

### 1. Update Your Branch

```bash
# Fetch latest changes from upstream
git fetch upstream
git rebase upstream/main

# Or merge if rebasing causes conflicts
git merge upstream/main
```

### 2. Push Your Changes

```bash
git push origin feature/your-feature-name
```

### 3. Create Pull Request

1. Go to [GitHub](https://github.com/qvidal01/camera-analytics)
2. Click "New Pull Request"
3. Select your branch
4. Fill out the PR template:
   - Clear title describing the change
   - Detailed description of what and why
   - Link to related issues
   - Screenshots (if UI changes)
   - Testing performed

### 4. PR Review

- Address reviewer feedback
- Keep CI checks passing (tests, linting, type checking)
- Update documentation if needed
- Squash commits if requested

## Project Structure

```
camera-analytics/
├── src/camera_analytics/      # Source code
│   ├── core/                  # Core functionality
│   │   ├── camera_manager.py
│   │   ├── detection_engine.py
│   │   └── ...
│   ├── config/                # Configuration
│   ├── utils/                 # Utilities
│   ├── api.py                 # FastAPI application
│   └── cli.py                 # CLI commands
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── docs/                      # Documentation
├── examples/                  # Example scripts
└── .github/workflows/         # CI/CD
```

## Adding a New Feature

### Example: Add New Camera Type

1. **Create camera source class** in `core/camera_manager.py`:
   ```python
   class MyCameraSource(CameraSource):
       async def connect(self) -> bool:
           # Implementation
           pass
   ```

2. **Update CameraType enum**:
   ```python
   class CameraType(Enum):
       MY_CAMERA = "my_camera"
   ```

3. **Update CameraManager.add_camera()**:
   ```python
   elif config.source_type == CameraType.MY_CAMERA:
       camera = MyCameraSource(config)
   ```

4. **Write tests** in `tests/unit/test_camera_manager.py`

5. **Update documentation** in `docs/cameras.md`

6. **Add example** in `examples/my_camera_example.py`

## Getting Help

- **Questions**: [GitHub Discussions](https://github.com/qvidal01/camera-analytics/discussions)
- **Issues**: [GitHub Issues](https://github.com/qvidal01/camera-analytics/issues)
- **Chat**: Join our [Discord](https://discord.gg/camera-analytics) (placeholder)

## Attribution

Contributors are recognized in:
- README.md "Contributors" section
- Git commit history
- Release notes

Thank you for contributing! 🎉
