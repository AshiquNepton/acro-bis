path = 'common/templates/common/masters/customer_form.html'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace("deleteUrl        : \"{% url 'common:delete_customer' %}\",", "deleteUrl        : \"{% url 'common:delete_customer' %}?pk={id}\",")
with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

path2 = 'financial/templates/financial/masters/vendor_form.html'
with open(path2, 'r', encoding='utf-8') as f:
    code2 = f.read()
code2 = code2.replace("deleteUrl        : \"{% url 'financial:delete_vendor' %}\",", "deleteUrl        : \"{% url 'financial:delete_vendor' %}?pk={id}\",")
with open(path2, 'w', encoding='utf-8') as f:
    f.write(code2)

print("Fixed templates")
