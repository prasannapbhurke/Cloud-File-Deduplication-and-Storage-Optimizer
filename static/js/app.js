document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('uploadForm');
  const fileInput = document.getElementById('fileInput');
  const dropZone = document.getElementById('dropZone');
  const filePreview = document.getElementById('filePreview');
  const previewName = document.getElementById('previewName');
  const previewSize = document.getElementById('previewSize');
  const btnCancelFile = document.getElementById('btnCancelFile');
  const btnSubmitUpload = document.getElementById('btnSubmitUpload');
  const uploadFeedback = document.getElementById('uploadFeedback');
  const terminalBody = document.getElementById('terminalBody');
  const btnClearLogs = document.getElementById('btnClearLogs');
  const btnReset = document.getElementById('btnReset');
  const btnRefreshFiles = document.getElementById('btnRefreshFiles');
  const filesTableBody = document.getElementById('filesTableBody');

  // Metrics elements
  const metricTotalFiles = document.getElementById('metricTotalFiles');
  const metricDuplicatesCount = document.getElementById('metricDuplicatesCount');
  const metricDedupRatio = document.getElementById('metricDedupRatio');
  const metricSavingsPct = document.getElementById('metricSavingsPct');
  const metricPhysicalStored = document.getElementById('metricPhysicalStored');
  const metricUniqueChunks = document.getElementById('metricUniqueChunks');
  const metricSpaceSaved = document.getElementById('metricSpaceSaved');
  const metricLogicalTotal = document.getElementById('metricLogicalTotal');
  const storageProgressBar = document.getElementById('storageProgressBar');
  const labelPhysical = document.getElementById('labelPhysical');
  const labelSaved = document.getElementById('labelSaved');

  let selectedFile = null;

  function appendLog(message, type = 'info') {
    const time = new Date().toLocaleTimeString();
    const logLine = document.createElement('div');
    logLine.className = `log-line log-${type}`;
    logLine.textContent = `[${time}] ${message}`;
    terminalBody.appendChild(logLine);
    terminalBody.scrollTop = terminalBody.scrollHeight;
  }

  function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // File selection handling
  function handleFileSelected(file) {
    if (!file) return;
    selectedFile = file;
    previewName.textContent = file.name;
    previewSize.textContent = `(${formatBytes(file.size)})`;
    dropZone.classList.add('hidden');
    filePreview.classList.remove('hidden');
    uploadFeedback.classList.add('hidden');
    appendLog(`Selected file: "${file.name}" (${formatBytes(file.size)})`, 'info');
  }

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  // Drag and Drop
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt.files && dt.files.length > 0) {
      fileInput.files = dt.files;
      handleFileSelected(dt.files[0]);
    }
  });

  btnCancelFile.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    dropZone.classList.remove('hidden');
    filePreview.classList.add('hidden');
  });

  btnClearLogs.addEventListener('click', () => {
    terminalBody.innerHTML = '';
    appendLog('Terminal logs cleared.', 'system');
  });

  // Modal elements
  const chunkModal = document.getElementById('chunkModal');
  const modalBackdrop = document.getElementById('modalBackdrop');
  const modalClose = document.getElementById('modalClose');
  const modalFileName = document.getElementById('modalFileName');
  const modalFileHash = document.getElementById('modalFileHash');
  const modalTotalChunks = document.getElementById('modalTotalChunks');
  const modalDedupChunks = document.getElementById('modalDedupChunks');
  const modalNewChunks = document.getElementById('modalNewChunks');
  const chunkBlocksGrid = document.getElementById('chunkBlocksGrid');
  const modalChunksTableBody = document.getElementById('modalChunksTableBody');

  // Fetch and update metrics
  async function updateStats() {
    try {
      const res = await fetch('api/stats');
      const data = await res.json();

      metricTotalFiles.textContent = data.total_files;
      const chunkDedupInfo = data.total_dedup_chunks ? ` (${data.total_dedup_chunks} block hits)` : '';
      metricDuplicatesCount.textContent = `${data.duplicate_files_count} duplicate files avoided${chunkDedupInfo}`;
      metricDedupRatio.textContent = data.deduplication_ratio;
      metricSavingsPct.textContent = `${data.savings_percentage}% physical space reduction`;
      metricPhysicalStored.textContent = data.total_physical_formatted;
      metricUniqueChunks.textContent = `${data.unique_chunks} unique chunks stored in cloud`;
      metricSpaceSaved.textContent = data.space_saved_formatted;
      metricLogicalTotal.textContent = `Logical Volume: ${data.total_logical_formatted}`;

      // Update storage progress bar
      const totalLogical = data.total_logical_bytes;
      const physical = data.total_physical_bytes;
      const saved = data.space_saved_bytes;

      if (totalLogical > 0) {
        const savedPct = (saved / totalLogical) * 100;
        storageProgressBar.style.width = `${savedPct.toFixed(1)}%`;
      } else {
        storageProgressBar.style.width = '0%';
      }

      labelPhysical.textContent = `Physical Stored: ${data.total_physical_formatted}`;
      labelSaved.textContent = `Redundant Data Saved: ${data.space_saved_formatted} (${data.savings_percentage}%)`;

    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }

  // Fetch and populate file list
  async function loadFiles() {
    try {
      const res = await fetch('api/files');
      const files = await res.json();

      if (files.length === 0) {
        filesTableBody.innerHTML = `
          <tr>
            <td colspan="9" class="text-center text-muted">No files uploaded yet. Upload a file above to test deduplication!</td>
          </tr>
        `;
        return;
      }

      filesTableBody.innerHTML = files.map(f => {
        const total = f.total_chunks || 1;
        let dedup = f.dedup_chunks || 0;

        // Fallback for legacy records or exact match records
        if (f.is_deduplicated && dedup === 0) {
          dedup = total;
        }

        const pct = Math.round((dedup / total) * 100);

        let statusTag = '';
        if (f.is_deduplicated || (dedup === total && total > 0)) {
          statusTag = `<span class="tag tag-dedup">⚡ 100% Deduplicated</span>`;
        } else if (dedup > 0) {
          statusTag = `<span class="tag tag-partial">🧩 Partial (${pct}% Saved)</span>`;
        } else {
          statusTag = `<span class="tag tag-unique">💾 Unique Payload</span>`;
        }

        const chunkSummary = `<span style="font-family: var(--font-mono); font-size: 0.8rem;"><strong>${dedup}</strong> / ${total} reused (${pct}%)</span>`;

        return `
          <tr>
            <td><strong>#${f.id}</strong></td>
            <td><strong>${escapeHtml(f.filename)}</strong></td>
            <td>${escapeHtml(f.user_name)}</td>
            <td>${formatBytes(f.file_size)}</td>
            <td class="hash-cell" title="${f.chunk_hash}">${f.chunk_hash.substring(0, 16)}...</td>
            <td>${chunkSummary}</td>
            <td>${statusTag}</td>
            <td style="font-size: 0.8rem; color: var(--text-secondary);">${f.upload_timestamp}</td>
            <td>
              <div class="action-btns">
                <a href="api/download/${f.id}" class="btn-action" title="Download Reconstructed File">⬇️</a>
                <button onclick="window.inspectChunks(${f.id})" class="btn-action btn-inspect" title="Inspect 64 KB Blocks">🔍 Blocks</button>
                <button onclick="window.deleteFileItem(${f.id})" class="btn-action btn-danger" title="Delete">🗑️</button>
              </div>
            </td>
          </tr>
        `;
      }).join('');

    } catch (err) {
      console.error('Error loading files:', err);
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Modal Functions
  function openModal() {
    chunkModal.classList.remove('hidden');
  }

  function closeModal() {
    chunkModal.classList.add('hidden');
  }

  modalClose.addEventListener('click', closeModal);
  modalBackdrop.addEventListener('click', closeModal);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !chunkModal.classList.contains('hidden')) {
      closeModal();
    }
  });

  // Global chunk inspector handler
  window.inspectChunks = async (fileId) => {
    try {
      appendLog(`[INSPECT] Fetching block map and chunk hashes for File #${fileId}...`, 'info');
      const res = await fetch(`api/file/${fileId}/chunks`);
      if (!res.ok) throw new Error('File not found');
      const data = await res.json();

      modalFileName.textContent = `${data.filename} (File #${data.file_id})`;
      modalFileHash.textContent = `Whole-File SHA-256: ${data.file_hash}`;
      modalTotalChunks.textContent = data.total_chunks;
      const pct = Math.round((data.dedup_chunks / (data.total_chunks || 1)) * 100);
      modalDedupChunks.textContent = `${data.dedup_chunks} (${pct}%)`;
      modalNewChunks.textContent = data.new_chunks;

      // Render Visual Block Map
      chunkBlocksGrid.innerHTML = '';
      const chunks = data.chunks || [];
      if (chunks.length === 0) {
        chunkBlocksGrid.innerHTML = '<span class="text-muted" style="font-size: 0.8rem;">Single-chunk legacy file.</span>';
      } else {
        chunks.forEach((c) => {
          const isReused = c.ref_count > 1;
          const block = document.createElement('div');
          block.className = `chunk-block ${isReused ? 'block-dedup' : 'block-new'}`;
          block.textContent = (c.chunk_index + 1);
          block.title = `Block #${c.chunk_index + 1}\nSHA-256: ${c.chunk_hash}\nSize: ${formatBytes(c.size_bytes)}\nRefs: ${c.ref_count}\nStatus: ${isReused ? 'Reused / Deduplicated' : 'Newly Stored'}`;
          chunkBlocksGrid.appendChild(block);
        });
      }

      // Render Chunk Table Rows
      modalChunksTableBody.innerHTML = chunks.map(c => {
        const isReused = c.ref_count > 1;
        const tag = isReused 
          ? `<span class="tag tag-dedup">⚡ Reused</span>`
          : `<span class="tag tag-unique">💾 New Block</span>`;

        return `
          <tr>
            <td><strong>#${c.chunk_index + 1}</strong></td>
            <td class="hash-cell" title="${c.chunk_hash}"><code>${c.chunk_hash}</code></td>
            <td>${formatBytes(c.size_bytes)}</td>
            <td><span class="badge">${c.ref_count} refs</span></td>
            <td>${tag}</td>
          </tr>
        `;
      }).join('');

      openModal();
    } catch (err) {
      console.error('Inspect error:', err);
      alert('Unable to load chunk details: ' + err.message);
    }
  };

  // Form submission / Upload
  uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      alert('Please select a file to upload.');
      return;
    }

    const userName = document.getElementById('userName').value;
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('user_name', userName);

    btnSubmitUpload.disabled = true;
    btnSubmitUpload.innerHTML = '<span>⚡ Slicing 64 KB Blocks & Hashing SHA-256...</span>';

    appendLog(`[INGEST] Slicing "${selectedFile.name}" (${formatBytes(selectedFile.size)}) into 64 KB blocks...`, 'info');

    try {
      const res = await fetch('api/upload', {
        method: 'POST',
        body: formData
      });

      const contentType = res.headers.get('content-type') || '';
      let data;
      if (contentType.includes('application/json')) {
        data = await res.json();
      } else {
        const errText = await res.text();
        throw new Error(`Server returned HTTP ${res.status}: ${errText.substring(0, 100)}`);
      }

      if (!res.ok) {
        throw new Error(data.error || `Upload failed with status ${res.status}`);
      }

      uploadFeedback.classList.remove('hidden');

      if (data.status === 'DEDUPLICATED') {
        uploadFeedback.className = 'upload-feedback feedback-dedup';
        uploadFeedback.innerHTML = `
          <strong>⚡ Exact Duplicate Intercepted! (100% Match)</strong><br>
          Whole-File SHA-256: <code>${data.file_hash.substring(0, 24)}...</code><br>
          <strong>Blocks:</strong> All ${data.total_chunks}/${data.total_chunks} blocks already exist in Cloud S3.<br>
          <strong>Physical Writes Bypassed:</strong> 0 bytes stored | Saved ${formatBytes(data.space_saved_bytes)}.
        `;
        appendLog(`[SHA-256] File Hash: ${data.file_hash}`, 'info');
        appendLog(`[100% DEDUP] All ${data.total_chunks} blocks matched existing cloud objects! 0 bytes written to disk.`, 'dedup');
        appendLog(`[SAVED] Net cloud storage saved: ${formatBytes(data.space_saved_bytes)}!`, 'dedup');

      } else if (data.status === 'PARTIALLY_DEDUPLICATED') {
        uploadFeedback.className = 'upload-feedback feedback-dedup';
        uploadFeedback.innerHTML = `
          <strong>🧩 Sub-File / Partial Deduplication Detected!</strong><br>
          Whole-File SHA-256: <code>${data.file_hash.substring(0, 24)}...</code><br>
          <strong>Blocks:</strong> ${data.dedup_chunks} reused (${data.dedup_percentage}%), only ${data.new_chunks} new block(s) written.<br>
          <strong>Physical Storage Written:</strong> ${formatBytes(data.physical_bytes_written)} | Space Saved: ${formatBytes(data.space_saved_bytes)}.
        `;
        appendLog(`[SHA-256] File Hash: ${data.file_hash}`, 'info');
        appendLog(`[PARTIAL DEDUP] Reused ${data.dedup_chunks}/${data.total_chunks} blocks. Wrote only ${data.new_chunks} changed blocks.`, 'dedup');
        appendLog(`[SAVED] Saved ${formatBytes(data.space_saved_bytes)} (${data.dedup_percentage}% space reduction)!`, 'dedup');

      } else {
        uploadFeedback.className = 'upload-feedback feedback-success';
        uploadFeedback.innerHTML = `
          <strong>💾 Unique File Stored!</strong><br>
          Whole-File SHA-256: <code>${data.file_hash.substring(0, 24)}...</code><br>
          <strong>Result:</strong> Sliced into ${data.total_chunks} blocks (64 KB each) and persisted to Cloud CAS.<br>
          <strong>Stored Size:</strong> ${formatBytes(data.physical_bytes_written)}.
        `;
        appendLog(`[SHA-256] File Hash: ${data.file_hash}`, 'info');
        appendLog(`[STORED] Persisted ${data.total_chunks} unique blocks to /chunks/...`, 'unique');
      }

      // Reset form selection
      selectedFile = null;
      fileInput.value = '';
      dropZone.classList.remove('hidden');
      filePreview.classList.add('hidden');

      // Refresh UI
      await updateStats();
      await loadFiles();

    } catch (err) {
      appendLog(`[ERROR] Upload failed: ${err.message}`, 'warn');
      uploadFeedback.className = 'upload-feedback';
      uploadFeedback.textContent = 'Upload failed. Check console for details.';
      uploadFeedback.classList.remove('hidden');
    } finally {
      btnSubmitUpload.disabled = false;
      btnSubmitUpload.innerHTML = '<span>Slice Chunks, Hash & Upload</span>';
    }
  });

  // Global delete handler
  window.deleteFileItem = async (fileId) => {
    if (!confirm(`Are you sure you want to delete file #${fileId}?`)) return;

    try {
      appendLog(`[DELETE] Requesting removal of file #${fileId}...`, 'info');
      const res = await fetch(`api/delete/${fileId}`, { method: 'POST' });
      const data = await res.json();

      if (data.success) {
        if (data.purged_physical_chunks > 0) {
          appendLog(`[PURGE] References dropped to 0! Permanently purged ${data.purged_physical_chunks} orphaned cloud blocks.`, 'warn');
        } else {
          appendLog(`[DEREF] File reference removed. Cloud blocks retained for other files sharing identical data.`, 'info');
        }
        await updateStats();
        await loadFiles();
      } else {
        alert(data.error || 'Failed to delete file');
      }
    } catch (err) {
      console.error('Delete error:', err);
    }
  };

  btnRefreshFiles.addEventListener('click', () => {
    loadFiles();
    updateStats();
  });

  btnReset.addEventListener('click', async () => {
    if (!confirm('This will wipe all metadata and cloud storage chunks. Continue?')) return;
    try {
      await fetch('api/reset', { method: 'POST' });
      appendLog('[RESET] Cloud storage and metadata catalog completely wiped.', 'warn');
      uploadFeedback.classList.add('hidden');
      await updateStats();
      await loadFiles();
    } catch (err) {
      console.error('Reset error:', err);
    }
  });

  // Initial load
  updateStats();
  loadFiles();
});
