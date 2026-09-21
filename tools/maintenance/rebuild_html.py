import re

path = 'inventory/templates/inventory/item_master_form.html'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Get the comment
comment_match = re.search(r'\{\% comment \%\}.*?\{\% endcomment \%\}', code, flags=re.DOTALL)
comment = comment_match.group(0) if comment_match else ''

# 2. Get the app_content_body
body_match = re.search(r'\{\% block app_content_body \%\}(.*?)\{\% endblock \%\}', code, flags=re.DOTALL)
body = body_match.group(1).strip() if body_match else '<div class="pf-page-wrapper" style="width:100%; min-height:100%; overflow-x:hidden;">\n    {% include \'common/includes/profile_form.html\' with fc=form_config %}\n</div>'

# 3. Get the Arabic translation script
trans_script = """<script>
document.addEventListener('DOMContentLoaded', function() {
    var nameInp = document.getElementById('id_ItemName');
    var shortInp = document.getElementById('id_ShortName');
    var localInp = document.getElementById('id_LocalName');

    if (nameInp) {
        nameInp.addEventListener('input', function() {
            var val = this.value || '';
            if (!val) return;
            if (shortInp && !shortInp.value) shortInp.value = val;
            if (localInp && !localInp.value) {
                fetch('https://api.mymemory.translated.net/get?q=' + encodeURIComponent(val) + '&langpair=en|ar')
                    .then(function(r) { return r.json(); })
                    .then(function(d) {
                        if (d && d.responseData && d.responseData.translatedText) {
                            localInp.value = d.responseData.translatedText;
                        }
                    })
                    .catch(function(e) { console.error('Translation error:', e); });
            }
        });
    }
});
</script>"""

# 4. Get the REAL app_js content
app_js_match = re.search(r'(<link rel="stylesheet".*)', code, flags=re.DOTALL)
if app_js_match:
    real_app_js = app_js_match.group(1).strip()
    real_app_js = re.sub(r'\{\% endblock \%\}', '', real_app_js)
    real_app_js = re.sub(r'<script>\s*document\.addEventListener\(\'DOMContentLoaded\', function\(\) \{\s*var nameInp = document\.getElementById\(\'id_ItemName\'\).*?</script>', '', real_app_js, flags=re.DOTALL)
else:
    real_app_js = ''

# Build the new file
new_code = f"""{{% extends 'inventory/base.html' %}}
{comment}
{{% load static %}}

{{% block title %}}{{{{ form_config.title }}}}{{% endblock %}}

{{% block app_content_body %}}
{body}
{{% endblock %}}

{{% block app_js %}}
{trans_script}

{real_app_js.strip()}
{{% endblock %}}
"""

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_code)
print('Rebuilt item_master_form.html cleanly')
