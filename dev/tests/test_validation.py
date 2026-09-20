from dev.validation import validate_order_payload

def test_missing_customer_email():
    try:
        validate_order_payload({'items': [{'product_id':1,'quantity':1}], 'customer': {}})
        assert False
    except Exception:
        assert True
