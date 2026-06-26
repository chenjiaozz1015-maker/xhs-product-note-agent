from app.services import poster_engine_adapter
from app.services.poster_engine_adapter import PosterRenderInput, render_posters


def test_adapter_imports_and_uses_default_pillow_engine(monkeypatch):
    captured = {}

    def fake_compose_posters(**kwargs):
        captured.update(kwargs)
        return ["/static/generated/fake_cover.png"]

    monkeypatch.setattr(poster_engine_adapter, "compose_posters", fake_compose_posters)

    result = render_posters(
        PosterRenderInput(
            input_image_path="app/static/uploads/sample.png",
            output_dir="app/static/generated",
            style="干货清单",
            category="食品饮品",
            product_name="水牛奶蛋糕",
            note_data={
                "cover_title": "水牛奶蛋糕，这几点值得看",
                "cover_subtitle": "食品饮品｜好物推荐｜干货清单",
                "selling_points": ["早餐下午茶都能搭"],
                "summary_title": "水牛奶蛋糕的 3 个体验点",
            },
        )
    )

    assert result == ["/static/generated/fake_cover.png"]
    assert captured["input_image_path"] == "app/static/uploads/sample.png"
    assert captured["style"] == "干货清单"
    assert captured["title"] == "水牛奶蛋糕，这几点值得看"
    assert captured["selling_points"] == ["早餐下午茶都能搭"]
