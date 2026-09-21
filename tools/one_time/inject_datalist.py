import re

path = 'inventory/templates/inventory/item_master_form.html'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# We'll inject the JS before the closing </script> tag at the bottom.
# But there might be multiple <script> tags. 
# We'll inject it just before {% endblock %}

js_code = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    var ic = document.getElementById('id_ItemCode');
    if (ic) {
        ic.setAttribute('list', 'itemcode-datalist');
        ic.setAttribute('autocomplete', 'off');
        var dl = document.createElement('datalist');
        dl.id = 'itemcode-datalist';
        document.body.appendChild(dl);
        
        var timer;
        ic.addEventListener('input', function() {
            clearTimeout(timer);
            var q = ic.value.trim();
            if (q.length < 1) return;
            timer = setTimeout(function() {
                fetch("{% url 'inventory:item_master_lookup' %}?q=" + encodeURIComponent(q))
                    .then(r => r.json())
                    .then(d => {
                        if (d.success) {
                            dl.innerHTML = '';
                            d.results.forEach(function(r) {
                                var opt = document.createElement('option');
                                opt.value = r.ItemCode;
                                opt.textContent = r.ItemName;
                                dl.appendChild(opt);
                            });
                        }
                    });
            }, 300);
        });
    }
});
</script>
{% endblock %}
"""

code = code.replace("{% endblock %}", js_code)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Injected datalist JS")
