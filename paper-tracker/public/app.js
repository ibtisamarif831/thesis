// State management
let papers = [];
let currentPaperId = null;
let isEditMode = false;

// DOM Elements
const papersList = document.getElementById('papers-list');
const emptyState = document.getElementById('empty-state');
const paperDetails = document.getElementById('paper-details');
const viewModeContainer = document.getElementById('view-mode-container');
const editModeForm = document.getElementById('edit-mode-form');

// View Elements
const viewTitle = document.getElementById('view-title');
const viewAuthors = document.getElementById('view-authors');
const viewStatusBadge = document.getElementById('view-status-badge');
const viewRelevance = document.getElementById('view-relevance');
const viewFileLink = document.getElementById('view-file-link');
const viewNotes = document.getElementById('view-notes');
const viewCitation = document.getElementById('view-citation');

// Form/Edit Elements
const editTitle = document.getElementById('edit-title');
const editAuthors = document.getElementById('edit-authors');
const editUrl = document.getElementById('edit-url');
const editStatus = document.getElementById('edit-status');
const editRelevance = document.getElementById('edit-relevance');
const editNotes = document.getElementById('edit-notes');
const editCitation = document.getElementById('edit-citation');

// Buttons & Actions
const btnSync = document.getElementById('btn-sync');
const btnSyncEmpty = document.getElementById('btn-sync-empty');
const btnAddManual = document.getElementById('btn-add-manual');
const btnEdit = document.getElementById('btn-edit');
const btnCancel = document.getElementById('btn-cancel');
const btnDelete = document.getElementById('btn-delete');
const btnCopyCitation = document.getElementById('btn-copy-citation');
const searchInput = document.getElementById('search-input');
const filterStatus = document.getElementById('filter-status');

// Stats Elements
const statTotal = document.getElementById('stat-total');
const statReading = document.getElementById('stat-reading');
const statCompleted = document.getElementById('stat-completed');

// API URL (same domain)
const API_BASE = '/api';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  fetchPapers();
  setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
  btnSync.addEventListener('click', syncLocalPDFs);
  btnSyncEmpty.addEventListener('click', syncLocalPDFs);
  btnAddManual.addEventListener('click', enterCreateMode);
  btnEdit.addEventListener('click', enterEditMode);
  btnCancel.addEventListener('click', exitEditMode);
  
  editModeForm.addEventListener('submit', handleFormSubmit);
  btnDelete.addEventListener('click', handlePaperDelete);
  
  btnCopyCitation.addEventListener('click', copyCitationToClipboard);
  
  searchInput.addEventListener('input', renderPapersList);
  filterStatus.addEventListener('change', renderPapersList);
}

// Fetch papers from API
async function fetchPapers() {
  try {
    const res = await fetch(`${API_BASE}/papers`);
    if (!res.ok) throw new Error('Failed to load papers');
    papers = await res.ok ? await res.json() : [];
    updateStats();
    renderPapersList();
    
    // Select first paper if details is open, or keep selected paper updated
    if (currentPaperId) {
      const exists = papers.find(p => p.id === currentPaperId);
      if (exists) {
        showPaperDetails(currentPaperId);
      } else {
        closeDetails();
      }
    }
  } catch (error) {
    console.error('Error fetching papers:', error);
    papersList.innerHTML = `<div class="error-msg">⚠️ Failed to load sources</div>`;
  }
}

// Update Stats display
function updateStats() {
  statTotal.textContent = papers.length;
  statReading.textContent = papers.filter(p => p.status === 'Reading').length;
  statCompleted.textContent = papers.filter(p => p.status === 'Completed').length;
}

// Render the papers in the sidebar list
function renderPapersList() {
  const searchTerm = searchInput.value.toLowerCase().trim();
  const statusFilter = filterStatus.value;
  
  const filtered = papers.filter(paper => {
    const matchesSearch = 
      paper.title.toLowerCase().includes(searchTerm) || 
      (paper.authors && paper.authors.toLowerCase().includes(searchTerm)) ||
      (paper.filename && paper.filename.toLowerCase().includes(searchTerm));
      
    const matchesStatus = statusFilter === 'all' || paper.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  if (filtered.length === 0) {
    papersList.innerHTML = `<div class="loading-spinner">No sources match filters</div>`;
    return;
  }

  papersList.innerHTML = '';
  filtered.forEach(paper => {
    const div = document.createElement('div');
    div.className = `paper-item ${paper.id === currentPaperId ? 'active' : ''}`;
    div.dataset.id = paper.id;
    
    let statusClass = 'to-read';
    if (paper.status === 'Reading') statusClass = 'reading';
    if (paper.status === 'Completed') statusClass = 'completed';

    const starsHtml = '★'.repeat(paper.relevance) + '☆'.repeat(5 - paper.relevance);

    div.innerHTML = `
      <div class="item-title">${paper.title}</div>
      <div class="item-meta">
        <span class="item-authors">${paper.authors || 'Unknown Author'}</span>
        <span class="badge ${statusClass}">${paper.status}</span>
      </div>
    `;
    
    div.addEventListener('click', () => {
      // Remove active class from other items
      document.querySelectorAll('.paper-item').forEach(item => item.classList.remove('active'));
      div.classList.add('active');
      showPaperDetails(paper.id);
    });
    
    papersList.appendChild(div);
  });
}

// Show paper details in main section
async function showPaperDetails(id) {
  try {
    const res = await fetch(`${API_BASE}/papers/${id}`);
    if (!res.ok) throw new Error('Failed to load paper details');
    const paper = await res.json();
    
    currentPaperId = paper.id;
    exitEditMode();
    
    // View Mode data binding
    viewTitle.textContent = paper.title;
    viewAuthors.textContent = paper.authors || 'No authors specified';
    
    // Status badge styling
    viewStatusBadge.className = 'badge';
    if (paper.status === 'To Read') viewStatusBadge.classList.add('to-read');
    if (paper.status === 'Reading') viewStatusBadge.classList.add('reading');
    if (paper.status === 'Completed') viewStatusBadge.classList.add('completed');
    viewStatusBadge.textContent = paper.status;
    
    // Relevance stars
    viewRelevance.textContent = '★'.repeat(paper.relevance) + '☆'.repeat(5 - paper.relevance);
    
    // Link / File Action
    if (paper.filename.startsWith('manual-')) {
      if (paper.url) {
        viewFileLink.href = paper.url;
        viewFileLink.textContent = '🔗 Open Link';
        viewFileLink.classList.remove('hidden');
      } else {
        viewFileLink.classList.add('hidden');
      }
    } else {
      // It is a local PDF in parent workspace directory
      viewFileLink.href = `../${paper.filename}`;
      viewFileLink.textContent = '📖 Open PDF';
      viewFileLink.classList.remove('hidden');
    }
    
    // Notes rendering
    viewNotes.innerHTML = parseMarkdown(paper.notes);
    
    // Citation
    if (paper.citation) {
      viewCitation.textContent = paper.citation;
      document.querySelector('.citation-section').classList.remove('hidden');
    } else {
      // Auto-generate basic BibTeX draft
      const defaultCitation = generateBibTeX(paper);
      viewCitation.textContent = defaultCitation;
      document.querySelector('.citation-section').classList.remove('hidden');
    }
    
    // Show details container
    emptyState.classList.add('hidden');
    paperDetails.classList.remove('hidden');
  } catch (error) {
    console.error('Error showing paper details:', error);
  }
}

// Close details panel
function closeDetails() {
  currentPaperId = null;
  paperDetails.classList.add('hidden');
  emptyState.classList.remove('hidden');
}

// Toggle Edit/Create modes
function enterEditMode() {
  const paper = papers.find(p => p.id === currentPaperId);
  if (!paper) return;
  
  isEditMode = true;
  
  // Bind form inputs
  editTitle.value = paper.title;
  editAuthors.value = paper.authors || '';
  editUrl.value = paper.url || '';
  editStatus.value = paper.status;
  editRelevance.value = paper.relevance;
  editNotes.value = paper.notes || '';
  editCitation.value = paper.citation || generateBibTeX(paper);
  
  // Show delete button only for manually added sources
  if (paper.filename.startsWith('manual-')) {
    btnDelete.classList.remove('hidden');
  } else {
    btnDelete.classList.add('hidden');
  }
  
  viewModeContainer.classList.add('hidden');
  editModeForm.classList.remove('hidden');
}

function enterCreateMode() {
  currentPaperId = null;
  isEditMode = true;
  
  // Clear form
  editTitle.value = '';
  editAuthors.value = '';
  editUrl.value = '';
  editStatus.value = 'To Read';
  editRelevance.value = '0';
  editNotes.value = '';
  editCitation.value = '';
  
  btnDelete.classList.add('hidden');
  
  emptyState.classList.add('hidden');
  paperDetails.classList.remove('hidden');
  viewModeContainer.classList.add('hidden');
  editModeForm.classList.remove('hidden');
}

function exitEditMode() {
  isEditMode = false;
  editModeForm.classList.add('hidden');
  viewModeContainer.classList.remove('hidden');
  
  if (!currentPaperId) {
    closeDetails();
  }
}

// Handle Form Submission (Save or Create)
async function handleFormSubmit(e) {
  e.preventDefault();
  
  const payload = {
    title: editTitle.value.trim(),
    authors: editAuthors.value.trim(),
    url: editUrl.value.trim(),
    status: editStatus.value,
    relevance: parseInt(editRelevance.value),
    notes: editNotes.value.trim(),
    citation: editCitation.value.trim()
  };

  try {
    let url = `${API_BASE}/papers`;
    let method = 'POST';
    
    if (currentPaperId) {
      url = `${API_BASE}/papers/${currentPaperId}`;
      method = 'PUT';
    }
    
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error('Failed to save paper');
    
    const data = await res.json();
    
    // Refresh list and reload details
    await fetchPapers();
    
    const targetId = currentPaperId || data.id;
    showPaperDetails(targetId);
    
  } catch (error) {
    console.error('Error saving paper:', error);
    alert('Failed to save changes. Please try again.');
  }
}

// Handle Delete Source
async function handlePaperDelete() {
  if (!currentPaperId) return;
  if (!confirm('Are you sure you want to delete this source?')) return;
  
  try {
    const res = await fetch(`${API_BASE}/papers/${currentPaperId}`, {
      method: 'DELETE'
    });
    
    if (!res.ok) throw new Error('Failed to delete paper');
    
    closeDetails();
    fetchPapers();
  } catch (error) {
    console.error('Error deleting paper:', error);
    alert('Failed to delete source.');
  }
}

// Trigger Workspace PDF Directory Sync
async function syncLocalPDFs() {
  const btn = this;
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '🔄 Scanning...';
  
  try {
    const res = await fetch(`${API_BASE}/scan`, { method: 'POST' });
    if (!res.ok) throw new Error('Scan API failed');
    const result = await res.json();
    
    alert(`${result.message} Found and imported ${result.addedCount} new PDFs.`);
    await fetchPapers();
  } catch (error) {
    console.error('Error syncing:', error);
    alert('Failed to scan workspace. Make sure the Node server is running.');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

// Copy Citation to clipboard
function copyCitationToClipboard() {
  const codeText = viewCitation.textContent;
  navigator.clipboard.writeText(codeText)
    .then(() => {
      const originalText = btnCopyCitation.textContent;
      btnCopyCitation.textContent = '✓ Copied!';
      setTimeout(() => {
        btnCopyCitation.textContent = originalText;
      }, 2000);
    })
    .catch(err => {
      console.error('Could not copy text: ', err);
    });
}

// Local Markdown parser
function parseMarkdown(text) {
  if (!text) return '<p class="text-muted"><em>No takeaways added yet. Click edit to write down your findings from this study.</em></p>';
  
  // Escape HTML
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  // Parse bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Parse headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
  
  // Parse lines to build clean list tags & paragraph breaks
  const lines = html.split('\n');
  let inList = false;
  let resultLines = [];
  
  for (let line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      if (!inList) {
        resultLines.push('<ul>');
        inList = true;
      }
      resultLines.push(`<li>${trimmed.substring(2)}</li>`);
    } else {
      if (inList) {
        resultLines.push('</ul>');
        inList = false;
      }
      if (trimmed === '') {
        resultLines.push('<p class="spacer"></p>');
      } else if (!trimmed.startsWith('<h') && !trimmed.startsWith('<ul>') && !trimmed.startsWith('<li>')) {
        resultLines.push(`<p>${line}</p>`);
      } else {
        resultLines.push(line);
      }
    }
  }
  if (inList) resultLines.push('</ul>');
  
  return resultLines.join('\n');
}

// Generate a BibTeX placeholder entry
function generateBibTeX(paper) {
  // Create a citation key from first author last name & year, or title first word
  let key = 'paper';
  if (paper.authors) {
    const firstAuthor = paper.authors.split(',')[0].split(' ')[0].toLowerCase().replace(/[^a-z]/g, '');
    key = `${firstAuthor}2026`; // default fallback year
  } else {
    key = paper.title.split(' ')[0].toLowerCase().replace(/[^a-z]/g, '') + '2026';
  }
  
  return `@article{${key},
  title = {${paper.title}},
  author = {${paper.authors || 'Unknown'}},
  journal = {Thesis Repository Source},
  year = {2026},
  url = {${paper.url || ''}}
}`;
}
