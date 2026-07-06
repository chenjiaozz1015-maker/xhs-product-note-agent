from app.services import poster_engine_adapter
from app.services.poster_engine_adapter import PosterRenderInput, render_posters, resolve_engine_type


def test_engine_type_defaults_to_pillow(monkeypatch):
    monkeypatch.setattr(poster_engine_adapter, "POSTER_ENGINE_TYPE", "")

    assert resolve_engine_type() == "pillow"


def test_adapter_uses_pillow_engine_when_configured(monkeypatch):
    captured = {}

    def fake_compose_posters(**kwargs):
        captured.update(kwargs)
        return ["/static/generated/fake_cover.png"]

    monkeypatch.setattr(poster_engine_adapter, "POSTER_ENGINE_TYPE", "pillow")
    monkeypatch.setattr(poster_engine_adapter, "compose_posters_enhanced", fake_compose_posters)

    result = render_posters(
        PosterRenderInput(
            product_image_path="app/static/uploads/sample.png",
            output_dir="app/static/generated",
            style="干货清单",
            category="食品饮品",
            product_name="水牛奶蛋糕",
            content_type="好物推荐",
            note_data={
                "cover_title": "水牛奶蛋糕，这几点值得看",
                "cover_subtitle": "食品饮品｜好物推荐｜干货清单",
                "selling_points": ["早餐下午茶都能搭"],
                "summary_title": "水牛奶蛋糕的 3 个体验点",
            },
        )
    )

    assert result.success is True
    assert result.engine_type == "pillow"
    assert result.image_paths == ["/static/generated/fake_cover.png"]
    assert captured["input_image_path"] == "app/static/uploads/sample.png"
    assert captured["style"] == "干货清单"
    assert captured["title"] == "水牛奶蛋糕，这几点值得看"
    assert captured["selling_points"] == ["早餐下午茶都能搭"]
    assert captured["category"] == "食品饮品"
    assert captured["content_type"] == "好物推荐"
    assert captured["product_name"] == "水牛奶蛋糕"


def test_external_placeholder_falls_back_to_pillow(monkeypatch):
    monkeypatch.setattr(poster_engine_adapter, "POSTER_ENGINE_TYPE", "external_placeholder")
    monkeypatch.setattr(
        poster_engine_adapter,
        "compose_posters_enhanced",
        lambda **kwargs: ["/static/generated/external_fallback.png"],
    )

    result = render_posters(
        PosterRenderInput(product_image_path="app/static/uploads/sample.png")
    )

    assert result.success is True
    assert result.engine_type == "pillow"
    assert result.image_paths == ["/static/generated/external_fallback.png"]
    assert result.error_message is not None


def test_invalid_engine_type_falls_back_to_pillow(monkeypatch):
    monkeypatch.setattr(poster_engine_adapter, "POSTER_ENGINE_TYPE", "mystery")
    monkeypatch.setattr(
        poster_engine_adapter,
        "compose_posters_enhanced",
        lambda **kwargs: ["/static/generated/fallback.png"],
    )

    result = render_posters(
        PosterRenderInput(product_image_path="app/static/uploads/sample.png")
    )

    assert result.success is True
    assert result.engine_type == "pillow"
    assert result.image_paths == ["/static/generated/fallback.png"]
