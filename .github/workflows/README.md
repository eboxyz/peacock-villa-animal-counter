# GitHub Actions Workflows

## Docker Build and Push

This workflow builds and pushes Docker images to GitHub Container Registry (GHCR).

### Triggers

- **Tags**: Pushes on semver tags (`v*.*.*`) and `latest` tag
- **Manual**: Can be triggered manually via GitHub Actions UI

### Workflow Steps

1. **Test**: Runs backend and frontend tests
2. **Build Frontend**: Builds React frontend for production
3. **Build and Push**: Builds Docker image and pushes to GHCR

### Image Tags

- `latest`: Always pushed (for both `latest` tag and semver tags)
- `{version}`: Version from semver tag (e.g., `1.0.0` for tag `v1.0.0`)

### Usage

To deploy a new version:

```bash
# Create and push a semver tag
git tag v1.0.0
git push origin v1.0.0

# Or push latest
git tag latest
git push origin latest
```

The image will be available at:
- `ghcr.io/yourusername/peacock-villa-animal-counter:latest`
- `ghcr.io/yourusername/peacock-villa-animal-counter:1.0.0`

### Permissions

The workflow uses `GITHUB_TOKEN` which is automatically provided. Make sure the repository has:
- Contents: read
- Packages: write

These are set in the workflow file.
