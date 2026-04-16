// ============================================================
// n8n "Generate SQL" Code Node — corrected version
// Fixes: $node['Webhook'] → $('Webhook').first()  (modern API)
//        Added explicit return [{ json: {...} }]
// ============================================================

const body = $('Webhook').first().json.body;
const msg = (body.message || '').toLowerCase();
const uid = parseInt(body.user_id || 0, 10);
const uname = body.user_name || '';
const original = body.message;

let query = null;
let isComplex = false;

// ── Count queries ──────────────────────────────────────────
if ((msg.includes('how many') || msg.includes('count')) && msg.includes('test')) {
    query = `
    SELECT COUNT(*) AS total
    FROM test_cases tc
    JOIN user_project_assignment upa ON tc.project_id = upa.project_id
    WHERE upa.user_id = ${uid}
  `.trim();

} else if ((msg.includes('how many') || msg.includes('count')) && msg.includes('defect')) {
    query = `
    SELECT COUNT(*) AS total
    FROM defects d
    JOIN user_project_assignment upa ON d.project_id = upa.project_id
    WHERE upa.user_id = ${uid}
  `.trim();

} else if ((msg.includes('how many') || msg.includes('count')) && msg.includes('project')) {
    query = `
    SELECT COUNT(*) AS total
    FROM projects p
    JOIN user_project_assignment upa ON p.id = upa.project_id
    WHERE upa.user_id = ${uid}
  `.trim();

    // ── Detail queries ─────────────────────────────────────────
} else if (msg.includes('defect') || msg.includes('bug')) {
    isComplex = true;
    query = `
    SELECT d.id, d.title, d.severity, d.status, p.name AS project
    FROM defects d
    JOIN projects p ON d.project_id = p.id
    JOIN user_project_assignment upa ON d.project_id = upa.project_id
    WHERE upa.user_id = ${uid}
    ORDER BY d.created_at DESC
    LIMIT 10
  `.trim();

} else if (msg.includes('test case') || msg.includes('test cases')) {
    isComplex = true;
    query = `
    SELECT tc.id, tc.title, tc.status, tc.priority, p.name AS project
    FROM test_cases tc
    JOIN projects p ON tc.project_id = p.id
    JOIN user_project_assignment upa ON tc.project_id = upa.project_id
    WHERE upa.user_id = ${uid}
    ORDER BY tc.created_at DESC
    LIMIT 10
  `.trim();

} else if (msg.includes('project') || msg.includes('projects')) {
    isComplex = true;
    query = `
    SELECT p.id, p.name, p.status, p.description
    FROM projects p
    JOIN user_project_assignment upa ON p.id = upa.project_id
    WHERE upa.user_id = ${uid}
    ORDER BY p.name
  `.trim();

} else if (msg.includes('release') || msg.includes('releases')) {
    isComplex = true;
    query = `
    SELECT r.id, r.name, r.status, r.release_date, p.name AS project
    FROM releases r
    JOIN projects p ON r.project_id = p.id
    JOIN user_project_assignment upa ON r.project_id = upa.project_id
    WHERE upa.user_id = ${uid}
    ORDER BY r.release_date DESC
    LIMIT 10
  `.trim();
}

// ── Required return format for n8n Code node ──────────────
return [
    {
        json: {
            query,
            isComplex,
            uid,
            uname,
            original,
            msg,
        },
    },
];
