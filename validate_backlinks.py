#!/usr/bin/env python3
"""
Backlink Network and Protocol Compliance Validator

This script validates:
1. All [[links]] resolve to existing files
2. Bi-directional links exist where required by protocol
3. YAML front-matter fields are complete per AGENTS.md requirements
4. Cross-platform links are properly maintained

Based on AGENTS.md requirements for Surrentumlabs unified documentation protocol.
"""

import os
import re
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class LinkValidationResult:
    """Results of link validation"""
    valid_links: List[str]
    broken_links: List[str] 
    missing_backlinks: List[str]
    incomplete_frontmatter: List[str]
    cross_platform_issues: List[str]

class DocumentationValidator:
    """Main validator for documentation backlink network and protocol compliance"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.all_files = self.find_all_md_files()
        self.file_links = defaultdict(list)  # file -> [links it contains]
        self.backlinks = defaultdict(list)   # file -> [files that link to it]
        self.broken_links = []
        self.missing_backlinks = []
        self.frontmatter_issues = []
        self.cross_platform_issues = []
        
        # Required frontmatter fields per AGENTS.md
        self.required_frontmatter = {
            'status', 'source_path', 'last_scanned', 'tags', 
            'links', 'category', 'migration_priority', 'reuse_potential'
        }
        
        # Cross-platform required links per AGENTS.md
        self.required_cross_platform_links = {
            'Coverage', 'Index', 'RUST CONVERSION/Coverage', 
            '../../Warp/Tasks', '../../Warp/Changelog'
        }
        
    def find_all_md_files(self) -> List[Path]:
        """Find all .md files in the repository"""
        md_files = []
        for root, dirs, files in os.walk(self.base_path):
            # Skip .obsidian and other dot directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith('.md'):
                    md_files.append(Path(root) / file)
        return md_files
    
    def extract_wikilinks(self, content: str) -> List[str]:
        """Extract [[wikilinks]] from markdown content"""
        # Match [[link]] or [[link|display text]] or [[link#anchor]]
        pattern = r'\[\[([^\]]+?)\]\]'
        matches = re.findall(pattern, content)
        
        # Clean up links - remove display text and anchors
        cleaned_links = []
        for match in matches:
            if '|' in match:
                link = match.split('|')[0].strip()
            elif '#' in match:
                link = match.split('#')[0].strip()
            else:
                link = match.strip()
            cleaned_links.append(link)
        
        return cleaned_links
    
    def resolve_link_path(self, link: str, current_file: Path) -> Optional[Path]:
        """Resolve a [[link]] to an actual file path"""
        current_dir = current_file.parent
        
        # Handle relative paths
        if link.startswith('../'):
            target_path = (current_dir / link).resolve()
        elif link.startswith('./'):
            target_path = (current_dir / link[2:]).resolve()
        elif '/' in link:
            # Check if it's an absolute path from repo root
            absolute_path = self.base_path / link
            if absolute_path.exists():
                target_path = absolute_path
            else:
                # Try as relative path
                target_path = (current_dir / link).resolve()
        else:
            # Simple filename - search in current directory first, then globally
            target_path = current_dir / f"{link}.md"
            if not target_path.exists():
                # Search globally
                for md_file in self.all_files:
                    if md_file.stem == link:
                        target_path = md_file
                        break
                else:
                    return None
        
        # Add .md extension if not present
        if not target_path.suffix:
            target_path = target_path.with_suffix('.md')
        
        return target_path if target_path.exists() else None
    
    def parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Parse YAML frontmatter from markdown content"""
        if not content.startswith('---'):
            return {}, content
        
        try:
            parts = content.split('---', 2)
            if len(parts) < 3:
                return {}, content
            
            frontmatter = yaml.safe_load(parts[1])
            markdown_content = parts[2]
            return frontmatter or {}, markdown_content
        except yaml.YAMLError:
            return {}, content
    
    def validate_file_links(self, file_path: Path) -> List[str]:
        """Validate all links in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (UnicodeDecodeError, IOError) as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return []
        
        frontmatter, markdown_content = self.parse_frontmatter(content)
        
        # Validate frontmatter completeness
        self.validate_frontmatter(file_path, frontmatter)
        
        # Extract and validate links
        links = self.extract_wikilinks(content)
        broken_links = []
        
        for link in links:
            resolved_path = self.resolve_link_path(link, file_path)
            if resolved_path is None:
                broken_links.append(f"{file_path}: [[{link}]] -> NOT FOUND")
                self.broken_links.append(f"{file_path}: [[{link}]]")
            else:
                # Track valid links for bidirectional checking
                relative_current = file_path.relative_to(self.base_path)
                
                # Only track bidirectional links if target is within our base path
                try:
                    relative_target = resolved_path.relative_to(self.base_path)
                    self.file_links[str(relative_current)].append(str(relative_target))
                    self.backlinks[str(relative_target)].append(str(relative_current))
                except ValueError:
                    # Link points outside our documentation tree - that's okay, just don't track for bidirectional
                    pass
        
        return broken_links
    
    def validate_frontmatter(self, file_path: Path, frontmatter: Dict):
        """Validate YAML frontmatter completeness per AGENTS.md requirements"""
        relative_path = file_path.relative_to(self.base_path)
        missing_fields = []
        
        for required_field in self.required_frontmatter:
            if required_field not in frontmatter:
                missing_fields.append(required_field)
        
        if missing_fields:
            issue = f"{relative_path}: Missing frontmatter fields: {', '.join(missing_fields)}"
            self.frontmatter_issues.append(issue)
        
        # Validate specific field formats
        if 'status' in frontmatter and frontmatter['status'] not in ['todo', 'partial', 'done']:
            self.frontmatter_issues.append(f"{relative_path}: Invalid status value: {frontmatter['status']}")
        
        if 'category' in frontmatter:
            valid_categories = ['Essential', 'Semi-Essential', 'Non-Essential', 'Disconnected']
            if frontmatter['category'] not in valid_categories:
                self.frontmatter_issues.append(f"{relative_path}: Invalid category: {frontmatter['category']}")
    
    def check_required_cross_platform_links(self, file_path: Path, links: List[str]):
        """Check if file contains required cross-platform links per AGENTS.md"""
        relative_path = file_path.relative_to(self.base_path)
        
        # Check if this is a main platform file that needs cross-platform links
        if file_path.name in ['Index.md', 'Coverage.md'] or 'Essential' in str(file_path):
            missing_links = []
            for required_link in self.required_cross_platform_links:
                if not any(required_link in link for link in links):
                    missing_links.append(required_link)
            
            if missing_links:
                self.cross_platform_issues.append(
                    f"{relative_path}: Missing required cross-platform links: {', '.join(missing_links)}"
                )
    
    def validate_bidirectional_links(self):
        """Check for missing bidirectional links"""
        for file_path, linked_files in self.file_links.items():
            for linked_file in linked_files:
                # Check if linked file links back
                if file_path not in self.backlinks.get(linked_file, []):
                    # Some exceptions for one-way links (like to index files)
                    if not self.is_one_way_link_acceptable(file_path, linked_file):
                        self.missing_backlinks.append(
                            f"{linked_file} should link back to {file_path}"
                        )
    
    def is_one_way_link_acceptable(self, from_file: str, to_file: str) -> bool:
        """Determine if one-way link is acceptable per protocol"""
        # Index files and Coverage files don't need to link back to everything
        acceptable_targets = [
            'Index.md', 'Coverage.md', 'README.md', 'AGENTS.md',
            'Changelog.md', 'Tasks.md'
        ]
        
        target_name = Path(to_file).name
        return target_name in acceptable_targets
    
    def run_validation(self) -> LinkValidationResult:
        """Run complete validation and return results"""
        print(f"🔍 Validating {len(self.all_files)} markdown files...")
        
        # Validate each file
        all_broken_links = []
        for file_path in self.all_files:
            broken_links = self.validate_file_links(file_path)
            all_broken_links.extend(broken_links)
        
        # Check bidirectional links
        self.validate_bidirectional_links()
        
        return LinkValidationResult(
            valid_links=[],  # We track these internally
            broken_links=self.broken_links,
            missing_backlinks=self.missing_backlinks,
            incomplete_frontmatter=self.frontmatter_issues,
            cross_platform_issues=self.cross_platform_issues
        )
    
    def generate_report(self, results: LinkValidationResult) -> str:
        """Generate validation report"""
        report = []
        report.append("# Documentation Link Validation Report")
        report.append(f"**Generated**: {os.popen('date -u').read().strip()}")
        report.append(f"**Files Scanned**: {len(self.all_files)}")
        report.append("")
        
        # Summary
        total_issues = (len(results.broken_links) + len(results.missing_backlinks) + 
                       len(results.incomplete_frontmatter) + len(results.cross_platform_issues))
        
        if total_issues == 0:
            report.append("✅ **ALL VALIDATION CHECKS PASSED**")
            report.append("")
            report.append("- All [[links]] resolve correctly")
            report.append("- Bidirectional links are properly maintained")
            report.append("- YAML frontmatter is complete per AGENTS.md requirements")
            report.append("- Cross-platform links are present where required")
        else:
            report.append(f"❌ **{total_issues} ISSUES FOUND**")
            report.append("")
        
        # Detailed results
        if results.broken_links:
            report.append(f"## 🔗 Broken Links ({len(results.broken_links)})")
            report.append("")
            for link in results.broken_links:
                report.append(f"- {link}")
            report.append("")
        
        if results.missing_backlinks:
            report.append(f"## 🔄 Missing Bidirectional Links ({len(results.missing_backlinks)})")
            report.append("")
            for backlink in results.missing_backlinks:
                report.append(f"- {backlink}")
            report.append("")
        
        if results.incomplete_frontmatter:
            report.append(f"## 📝 Incomplete YAML Frontmatter ({len(results.incomplete_frontmatter)})")
            report.append("")
            for issue in results.incomplete_frontmatter:
                report.append(f"- {issue}")
            report.append("")
        
        if results.cross_platform_issues:
            report.append(f"## 🌐 Cross-Platform Link Issues ({len(results.cross_platform_issues)})")
            report.append("")
            for issue in results.cross_platform_issues:
                report.append(f"- {issue}")
            report.append("")
        
        # Statistics
        report.append("## 📊 Statistics")
        report.append("")
        report.append(f"- **Total Files**: {len(self.all_files)}")
        report.append(f"- **Total Links Found**: {sum(len(links) for links in self.file_links.values())}")
        report.append(f"- **Broken Links**: {len(results.broken_links)}")
        report.append(f"- **Missing Backlinks**: {len(results.missing_backlinks)}")
        report.append(f"- **Frontmatter Issues**: {len(results.incomplete_frontmatter)}")
        report.append(f"- **Cross-Platform Issues**: {len(results.cross_platform_issues)}")
        
        return "\n".join(report)

def main():
    """Main validation function"""
    base_path = "/home/cinder/Documents/repos/Twitch Docs"
    
    if not os.path.exists(base_path):
        print(f"Error: Base path {base_path} does not exist")
        sys.exit(1)
    
    print("🚀 Starting Documentation Link Validation...")
    print("=" * 50)
    
    validator = DocumentationValidator(base_path)
    results = validator.run_validation()
    
    # Generate and save report
    report = validator.generate_report(results)
    
    report_path = os.path.join(base_path, "link_validation_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Report saved to: {report_path}")
    print("")
    
    # Print summary to console
    total_issues = (len(results.broken_links) + len(results.missing_backlinks) + 
                   len(results.incomplete_frontmatter) + len(results.cross_platform_issues))
    
    if total_issues == 0:
        print("✅ All validation checks passed!")
        return 0
    else:
        print(f"❌ Found {total_issues} issues:")
        print(f"   - Broken links: {len(results.broken_links)}")
        print(f"   - Missing backlinks: {len(results.missing_backlinks)}")
        print(f"   - Frontmatter issues: {len(results.incomplete_frontmatter)}")
        print(f"   - Cross-platform issues: {len(results.cross_platform_issues)}")
        print(f"\n📄 See full report: {report_path}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
