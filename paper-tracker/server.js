const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const db = require('./database');

const app = express();
const PORT = process.env.PORT || 3030;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Helper to format filename into a readable title
function formatTitle(filename) {
  // Strip extension
  let base = filename.replace(/\.pdf$/i, '');
  // Replace underscores and hyphens with spaces
  base = base.replace(/[_-]/g, ' ');
  // Capitalize first letter of each word
  return base.split(' ').map(word => {
    if (!word) return '';
    return word.charAt(0).toUpperCase() + word.slice(1);
  }).join(' ');
}

// Route to scan folder for PDF papers
app.post('/api/scan', (req, res) => {
  const parentDir = path.join(__dirname, '..');
  
  fs.readdir(parentDir, (err, files) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to read workspace directory: ' + err.message });
    }

    const pdfFiles = files.filter(file => file.toLowerCase().endsWith('.pdf'));
    let addedCount = 0;
    let checkedCount = 0;

    if (pdfFiles.length === 0) {
      return res.json({ message: 'No PDF files found to scan.', added: 0 });
    }

    pdfFiles.forEach(file => {
      // Check if file already exists in db
      db.get('SELECT id FROM papers WHERE filename = ?', [file], (queryErr, row) => {
        checkedCount++;
        
        if (queryErr) {
          console.error('Error querying DB during scan:', queryErr);
        } else if (!row) {
          // If it doesn't exist, insert it
          const title = formatTitle(file);
          const stmt = db.prepare('INSERT INTO papers (filename, title, status) VALUES (?, ?, ?)');
          stmt.run(file, title, 'To Read', (insertErr) => {
            if (insertErr) {
              console.error('Error inserting paper:', insertErr.message);
            }
          });
          stmt.finalize();
          addedCount++;
        }

        if (checkedCount === pdfFiles.length) {
          res.json({ message: `Scan completed successfully.`, addedCount });
        }
      });
    });
  });
});

// GET all papers
app.get('/api/papers', (req, res) => {
  db.all('SELECT * FROM papers ORDER BY updated_at DESC', [], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    res.json(rows);
  });
});

// GET single paper
app.get('/api/papers/:id', (req, res) => {
  db.get('SELECT * FROM papers WHERE id = ?', [req.params.id], (err, row) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    if (!row) {
      return res.status(404).json({ error: 'Paper not found' });
    }
    res.json(row);
  });
});

// POST manually add a paper/source
app.post('/api/papers', (req, res) => {
  const { title, authors, url, status, relevance, notes, citation } = req.body;
  if (!title) {
    return res.status(400).json({ error: 'Title is required' });
  }

  // Create a unique filename-like tag for manual items
  const filename = `manual-${Date.now()}`;

  const stmt = db.prepare(`
    INSERT INTO papers (filename, title, authors, url, status, relevance, notes, citation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);

  stmt.run(
    filename,
    title,
    authors || '',
    url || '',
    status || 'To Read',
    relevance || 0,
    notes || '',
    citation || '',
    function (err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json({ id: this.lastID, filename, title });
    }
  );
  stmt.finalize();
});

// PUT update a paper
app.put('/api/papers/:id', (req, res) => {
  const { title, authors, url, status, relevance, notes, citation } = req.body;
  
  db.run(
    `UPDATE papers SET 
      title = ?, 
      authors = ?, 
      url = ?, 
      status = ?, 
      relevance = ?, 
      notes = ?, 
      citation = ?, 
      updated_at = CURRENT_TIMESTAMP
     WHERE id = ?`,
    [title, authors, url, status, relevance, notes, citation, req.params.id],
    function(err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      if (this.changes === 0) {
        return res.status(404).json({ error: 'Paper not found' });
      }
      res.json({ message: 'Paper updated successfully' });
    }
  );
});

// DELETE a paper
app.delete('/api/papers/:id', (req, res) => {
  db.run('DELETE FROM papers WHERE id = ?', [req.params.id], function(err) {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    if (this.changes === 0) {
      return res.status(404).json({ error: 'Paper not found' });
    }
    res.json({ message: 'Paper deleted successfully' });
  });
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
