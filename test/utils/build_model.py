def build_model_from_factory_dict(model_cls, factory_dict):
    valid_keys = model_cls.__table__.columns.keys()
    filtered = {k: v for k, v in factory_dict.items() if k in valid_keys}
    return model_cls(**filtered)
