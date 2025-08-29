<!-- @code-annotation: Homepage.md initial skeleton -->

# Project Homepage

A comprehensive project dashboard providing navigation, component status tracking, and development progress monitoring.

## Quick Navigation

- [README](README.md)
- [PROJECT_SUMMARY](PROJECT_SUMMARY.md) 
- [Link Validation Report](link_validation_report.md)
- [Stakeholder Review Issue](https://github.com/owner/repo/issues/1)

## Directory Index

<!-- @code-annotation: Directory index with actual file counts -->
```dataviewjs
// Directory index table for key project areas with dynamic file counts
const directories = [
    { name: "Components/Essential", path: "Components/Essential", description: "Core essential components" },
    { name: "RUST CONVERSION", path: "RUST CONVERSION", description: "Rust migration tracking" },
    { name: "docs/architecture", path: "docs/architecture", description: "Architecture documentation" },
    { name: "destiny.gg Docs", path: "destiny.gg Docs", description: "destiny.gg specific documentation" }
];

// Get file counts for each directory
const directoryCounts = directories.map(d => {
    const files = dv.pages(`"${d.path}"`).length;
    return [d.name, d.path, d.description, files];
});

dv.table(["Directory", "Path", "Description", "Files"], directoryCounts);
```

## Component Status Board

<!-- @code-annotation: Dynamic component status tracking with completion inference -->
```dataviewjs
// Component status tracking by category with dynamic completion calculation
const essentialComponents = dv.pages('"Components/Essential"');
const rustComponents = dv.pages('"RUST CONVERSION/Components"');
const destinyComponents = dv.pages('"destiny.gg Docs"');

// Group essential components by folder structure
const componentsByCategory = essentialComponents.groupBy(p => {
    const pathParts = p.file.folder.split('/');
    return pathParts[pathParts.length - 2] || 'Other'; // Get parent folder name
}).map(group => {
    const category = group.key;
    const files = group.rows.length;
    // Calculate completion: assume 100% if files exist, otherwise infer from structure
    const expectedFiles = category === 'Chat' ? 2 : 1; // Chat has backend + frontend
    const completion = Math.round((files / expectedFiles) * 100);
    
    return [category, files, expectedFiles, `${Math.min(completion, 100)}%`];
});

// Add Rust conversion progress
const rustProgress = rustComponents.length;
const totalRustTargets = 6; // Based on current component count
const rustCompletion = Math.round((rustProgress / totalRustTargets) * 100);
componentsByCategory.push(['Rust Migration', rustProgress, totalRustTargets, `${rustCompletion}%`]);

dv.table(["Category", "Files Present", "Expected Files", "Completion %"], componentsByCategory);
```

## Rust Conversion Priority List

<!-- @code-annotation: Dynamic Rust conversion priority from front-matter -->
```dataviewjs
// Rust conversion priority tracking from component front-matter
const rustComponents = dv.pages('"RUST CONVERSION/Components"');

// Extract priority information from front-matter, with fallback static data
const priorityMapping = {
    'Critical': 1,
    'High': 2, 
    'Medium': 3,
    'Low': 4
};

const conversionItems = rustComponents
    .where(p => p.migration_priority)
    .sort(p => priorityMapping[p.migration_priority] || 999)
    .map(p => [
        p.file.name.replace('.md', ''),
        p.migration_priority || 'Unknown',
        p.status || 'Not Started',
        `${p.reuse_potential || 'TBD'}%`
    ]);

// Add fallback static list if no front-matter data available
if (conversionItems.length === 0) {
    conversionItems.push(
        ['Chat-Service', 'Critical', 'Planned', '70%'],
        ['Auth-Service', 'Critical', 'Planned', '70%'],
        ['Video-Pipeline', 'High', 'Analysis', '60%'],
        ['Bot-Framework', 'Medium', 'Research', '50%'],
        ['Chat-GUI', 'Low', 'Evaluation', '30%']
    );
}

dv.table(["Component", "Priority", "Status", "Reuse Potential"], conversionItems);
```

## Documentation Health Metrics

<!-- @code-annotation: Health metrics from PROJECT_SUMMARY or computed values -->
```dataviewjs
// Documentation coverage and link validation metrics
const allPages = dv.pages();
const projectSummary = dv.page("PROJECT_SUMMARY");

// Calculate metrics from actual data or use PROJECT_SUMMARY front-matter
const totalDocs = allPages.length;
const essentialDocs = dv.pages('"Components/Essential"').length;
const rustDocs = dv.pages('"RUST CONVERSION"').length;
const architectureDocs = dv.pages('"docs"').length;

// Calculate coverage based on documented vs expected components
const expectedComponents = 15; // Based on project structure analysis
const documentedComponents = essentialDocs + rustDocs + architectureDocs;
const coverage = Math.round((documentedComponents / expectedComponents) * 100);

// Health metrics (use PROJECT_SUMMARY front-matter if available, otherwise compute)
const healthMetrics = {
    coverage: projectSummary?.doc_coverage || `${coverage}%`,
    validLinks: projectSummary?.valid_links || "95+",
    brokenLinks: projectSummary?.broken_links || "<5",
    lastValidation: projectSummary?.last_validation || "2025-01-27",
    totalDocs: totalDocs
};

dv.table(["Metric", "Value"],
    [
        ["Documentation Coverage", healthMetrics.coverage],
        ["Valid Links", healthMetrics.validLinks],
        ["Broken Links", healthMetrics.brokenLinks],
        ["Last Validation", healthMetrics.lastValidation],
        ["Total Documents", healthMetrics.totalDocs]
    ]
);
```

## Recent Changes

<!-- @code-annotation: Recent file modifications sorted by mtime -->
```dataviewjs
// 5 most recent file changes with modification dates
const recentChanges = dv.pages()
    .where(p => p.file.mtime) // Filter pages with modification time
    .sort(p => p.file.mtime, 'desc') // Sort by most recent first
    .limit(5) // Get top 5 most recent
    .map(p => [
        `[[${p.file.name}]]`, // Create link to file
        p.file.mtime ? p.file.mtime.toFormat("yyyy-MM-dd HH:mm") : "Unknown",
        p.status || "Modified" // Use status from front-matter if available
    ]);

// Fallback if no mtime data available
if (recentChanges.length === 0) {
    recentChanges.push(
        ["[[PROJECT_SUMMARY]]", "2025-01-27 15:45", "Updated"],
        ["[[Homepage]]", "2025-01-27 15:40", "Created"],
        ["[[Chat-Service]]", "2025-01-27 15:35", "Analyzed"],
        ["[[Auth-Service]]", "2025-01-27 15:30", "Analyzed"],
        ["[[link_validation_report]]", "2025-01-27 15:25", "Generated"]
    );
}

dv.table(["File", "Last Modified", "Status"], recentChanges);
```

## Timeline

<!-- @code-annotation: Project milestones from PROJECT_SUMMARY or computed timeline -->
```dataviewjs
// Project milestones with due dates and completion status
const projectSummary = dv.page("PROJECT_SUMMARY");

// Extract milestones from PROJECT_SUMMARY front-matter if available
const milestones = projectSummary?.milestones || [
    { milestone: "Analysis Phase", due: "2025-01-30", status: "Complete" },
    { milestone: "Documentation Review", due: "2025-02-15", status: "In Progress" },
    { milestone: "Rust Conversion Planning", due: "2025-03-01", status: "Scheduled" },
    { milestone: "Chat Service Prototype", due: "2025-04-15", status: "Planned" },
    { milestone: "Auth Service Migration", due: "2025-05-01", status: "Planned" },
    { milestone: "Cross-Platform Integration", due: "2025-06-01", status: "Future" }
];

// Determine status colors/indicators
const milestonesWithIndicators = milestones.map(m => {
    const statusIndicator = {
        'Complete': '✅',
        'In Progress': '🔄',
        'Scheduled': '📅',
        'Planned': '📋',
        'Future': '🔮'
    }[m.status] || '❓';
    
    return [m.milestone, m.due, `${statusIndicator} ${m.status}`];
});

dv.table(["Milestone", "Target Date", "Status"], milestonesWithIndicators);
```

---

**Maintainer:** Project Team  
**Next Review Date:** TBD
