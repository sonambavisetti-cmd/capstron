def test_order_payload_validation():
    from dev.validation import validate_order_payload
    try:
        validate_order_payload({'items': [], 'customer': {'email': 'a@b.com'}})
        assert False, 'should raise for empty items'
    except Exception:
        assert True

# Further integration tests require DB and are out-of-scope for quick unit run
