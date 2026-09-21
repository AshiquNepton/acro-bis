import re

path = 'inventory/templates/inventory/item_master_form.html'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

pattern = r'function imResetSelectItemFields\(\) \{.*?imCloseAllSelectItemDropdowns\(\);\s*\}'

replacement = """function imResetSelectItemFields() {
    var itemInp = document.getElementById('im-si-item-inp');
    var g1Inp = document.getElementById('im-si-g1-inp');
    var g2Inp = document.getElementById('im-si-g2-inp');
    var g3Inp = document.getElementById('im-si-g3-inp');
    var g4Inp = document.getElementById('im-si-g4-inp');
    var g5Inp = document.getElementById('im-si-g5-inp');
    var catInp = document.getElementById('im-si-cat-inp');
    var valInp = document.getElementById('im-si-val-inp');
    var valChk = document.getElementById('im-si-val-chk');

    if (itemInp) {
        itemInp.value = (document.getElementById('id_ItemText') || {}).value || '';
        itemInp.style.background = '#d4e6ff';
        setTimeout(function() { itemInp.focus(); }, 50);
    }
    if (g1Inp) g1Inp.value = (document.getElementById('id_ItemGroup1Text') || {}).value || '';
    if (g2Inp) g2Inp.value = (document.getElementById('id_ItemGroup2Text') || {}).value || '';
    if (g3Inp) g3Inp.value = (document.getElementById('id_ItemGroup3Text') || {}).value || '';
    if (g4Inp) g4Inp.value = (document.getElementById('id_ItemGroup4Text') || {}).value || '';
    if (g5Inp) g5Inp.value = (document.getElementById('id_ItemGroup5Text') || {}).value || '';

    // Original catInp / valInp logic
    var currentBrand = (document.getElementById('id_Brand') || {}).value || '';
    var currentCat = (document.getElementById('id_Category') || {}).value || '';
    if (catInp) {
        catInp.value = currentBrand && currentCat ? (currentBrand + ' / ' + currentCat) : (currentBrand || currentCat || '');
        catInp.style.background = '#ffffff';
    }
    if (valInp) {
        valInp.value = '';
        valInp.style.background = '#ffffff';
    }
    if (valChk) {
        valChk.checked = true;
        if (valInp) valInp.disabled = false;
    }

    imCloseAllSelectItemDropdowns();
}"""

new_code = re.sub(pattern, replacement, code, flags=re.DOTALL)
with open(path, 'w', encoding='utf-8') as f:
    f.write(new_code)
print("Fixed imResetSelectItemFields")
