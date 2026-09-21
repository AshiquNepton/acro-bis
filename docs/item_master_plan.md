# Proposed Code Modifications

Here are the precise changes that will be applied. By targeting specific files and avoiding fragile regex replacements, we guarantee that the UOM table and the rest of the form will not break.

### 1. `imNew` Alert Logic
**File:** `inventory/templates/inventory/item_master_form.html`
```javascript
// We will replace the existing imNew() with:
function imNew() {
    var itemName = document.querySelector('[name="ItemName"]');
    if (itemName && itemName.value.trim() !== '') {
        showConfirm('Clear form for a new item?', function(confirmed) { 
            if (confirmed) window.location.href = window.location.pathname; 
        }, 'warning', 'New Item');
    } else {
        // Form is empty, just clear silently
        window.location.href = window.location.pathname;
    }
}
```

### 2. ItemCode Auto-Increment
**File:** `inventory/views/item_master.py`
```python
def generate_next_item_code(db_alias: str = None) -> str:
    # Instead of looking for exactly 'ITM-', we will dynamically find the last numeric ID:
    ...
    cur.execute('SELECT "ItemCode" FROM "InventoryItems" ORDER BY "ItemID" DESC LIMIT 1')
    row = cur.fetchone()
    if not row or not row[0]: return 'ITM-0001'
    code = str(row[0])
    match = re.search(r'(\d+)$', code)
    if match:
        prefix, num_str = code[:match.start()], match.group(1)
        return f"{prefix}{int(num_str) + 1:0{len(num_str)}d}"
    return f"{code}-0001"
```

### 3. ItemCode Search Behavior
**File:** `common/static/common/js/profile_form.js`
We will wrap the `input` event listener inside `_initLookup` in an `if (!cfg.disableAutoLookup)` check.
**File:** `item_master_form.html`
We will add `disableAutoLookup: true` to `window._pfConfig['item-master-form']`. This ensures it only fetches on click. (Note: A true dropdown list requires building a separate datalist/API, but this will stop the auto-fetch).

### 4 & 5. ShortName Sync & Arabic Translation
**File:** `inventory/templates/inventory/item_master_form.html`
```javascript
// We will safely inject this listener on DOMContentLoaded:
var nameInp = document.getElementById('id_ItemName');
var shortInp = document.getElementById('id_ShortName');
var localInp = document.getElementById('id_LocalName');

if (nameInp) {
    nameInp.addEventListener('input', function() {
        var val = this.value || '';
        if (shortInp && !shortInp.value) shortInp.value = val;
        if (localInp && !localInp.value) {
            // Free API translation to Arabic
            fetch('https://api.mymemory.translated.net/get?q=' + encodeURIComponent(val) + '&langpair=en|ar')
                .then(r => r.json())
                .then(d => {
                    if (d && d.responseData) localInp.value = d.responseData.translatedText;
                });
        }
    });
}
```

### 6. Bin Location Duplicate Check
**File:** `common/static/common/js/list_modal.js`
```javascript
// Inside ListModal.prototype._onEnterKey, we match the group_setup duplicate logic:
var dupIdx = this.rows.findIndex(function(r, i) {
    return i !== idx && (r.value || '').trim().toLowerCase() === currentVal.toLowerCase();
});
if (dupIdx !== -1) {
    this.rows[idx].value = ''; // clear current
    this.renderRows();
    this._focusRow(dupIdx); // jump to existing
    if (window.showToast) window.showToast('Duplicate entry found.', 'warning');
    return;
}
```

### 7, 8, 9, 10. Form Dictionary Updates (General Tab)
**File:** `inventory/views/item_master.py`
We will carefully modify the Python dictionary `tabs` array:
- Remove `field('BrandName'...)` and `field('CategoryName'...)` lines cleanly.
- Change `field('FixedPrice', ...)` to:
  `field('FixedPrice', 'Fixed Price', '3', options=[{'value':'1', 'label':'Yes'}, {'value':'0', 'label':'No'}], value='0'),`
- To fix the layout without breaking columns (like what happened last time), we will insert the CSS layout hack *inside* the existing first column, rather than accidentally pushing all columns over:
  `{'name': 'custom_css', 'type': 'custom_html', 'html': '<style>.pf-field:has(#id_MinStock), ... { display: inline-block; width: 48%; }</style>'},`

---
**Does this precise plan meet your approval? If so, click Proceed.**
