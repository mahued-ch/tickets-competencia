from app.services.catalog_service import CatalogService


class TestCatalogCsvTemplate:
    def test_get_template_competitor_stores(self, db_session):
        svc = CatalogService(db_session)
        csv = svc.get_template_csv("competitor-stores")
        assert csv is not None
        assert "business_code" in csv
        assert "store_code" in csv
        assert "WMT" in csv

    def test_get_template_chedraui_products(self, db_session):
        svc = CatalogService(db_session)
        csv = svc.get_template_csv("chedraui-products")
        assert csv is not None
        assert "sku" in csv
        assert "upc" in csv

    def test_get_template_competitor_mappings(self, db_session):
        svc = CatalogService(db_session)
        csv = svc.get_template_csv("competitor-mappings")
        assert csv is not None
        assert "business_code" in csv
        assert "match_type" in csv

    def test_get_template_nearby_stores(self, db_session):
        svc = CatalogService(db_session)
        csv = svc.get_template_csv("nearby-stores")
        assert csv is not None
        assert "nearby_chedraui_store_code" in csv

    def test_get_template_unknown(self, db_session):
        svc = CatalogService(db_session)
        assert svc.get_template_csv("unknown-catalog") is None


class TestCatalogCsvImport:
    def test_import_competitor_stores(self, db_session):
        svc = CatalogService(db_session)
        csv_content = "business_code,store_code,store_name,address,is_active\nWMT,1001,Walmart Test,Address 1,true\nBRS,2001,Bodega Test,Address 2,true\n"
        result = svc.import_csv("competitor-stores", csv_content)
        assert result["imported"] == 2
        assert result["errors"] == []
        rows = svc.list_competitor_stores()
        assert len(rows) == 2

    def test_import_chedraui_products(self, db_session):
        svc = CatalogService(db_session)
        csv_content = "sku,upc,description,list_price,department_code,sub_department_code,class_code,subclass_code,is_active\nCHD001,750001,Product Test,99.99,1,10,100,1000,true\nCHD002,750002,Product Test 2,49.99,2,20,200,2000,true\n"
        result = svc.import_csv("chedraui-products", csv_content)
        assert result["imported"] == 2
        rows = svc.list_chedraui_products()
        assert len(rows) == 2
        assert rows[0]["sku"] == "CHD001"

    def test_import_competitor_mappings(self, db_session):
        svc = CatalogService(db_session)
        csv_content = "business_code,competitor_code,competitor_description,chedraui_product_id,match_type,confidence,is_active\nWMT,P001,Product Mapping 1,1,MANUAL,0.95,true\n"
        result = svc.import_csv("competitor-mappings", csv_content)
        assert result["imported"] == 1
        rows = svc.list_mappings()
        assert len(rows) == 1

    def test_import_nearby_stores(self, db_session):
        svc = CatalogService(db_session)
        csv_content = "business_code,store_code,nearby_chedraui_store_code,distance_km,is_active\nWMT,1001,CHD001,5.5,true\nWMT,1001,CHD002,3.2,true\n"
        result = svc.import_csv("nearby-stores", csv_content)
        assert result["imported"] == 2
        rows = svc.list_nearby_stores()
        assert len(rows) == 2

    def test_import_with_unknown_columns(self, db_session):
        svc = CatalogService(db_session)
        csv_content = "business_code,unknown_col,store_code\nWMT,X,1001\n"
        import pytest
        with pytest.raises(ValueError, match="UNKNOWN_COLUMNS"):
            svc.import_csv("competitor-stores", csv_content)

    def test_import_unknown_catalog(self, db_session):
        svc = CatalogService(db_session)
        import pytest
        with pytest.raises(ValueError, match="UNKNOWN_CATALOG"):
            svc.import_csv("invalid", "a,b\n1,2\n")

    def test_import_empty_csv(self, db_session):
        svc = CatalogService(db_session)
        import pytest
        with pytest.raises(ValueError, match="EMPTY_CSV"):
            svc.import_csv("competitor-stores", "")

    def test_import_case_insensitive_headers(self, db_session):
        svc = CatalogService(db_session)
        csv_content = "BUSINESS_CODE,STORE_CODE,STORE_NAME\nWMT,1001,Walmart\n"
        result = svc.import_csv("competitor-stores", csv_content)
        assert result["imported"] == 1

    def test_import_boolean_coercion(self, db_session):
        svc = CatalogService(db_session)
        csv_content = "business_code,store_code,is_active\nWMT,1001,false\nBRS,2001,0\nSOR,3001,no\n"
        result = svc.import_csv("competitor-stores", csv_content)
        assert result["imported"] == 3
        rows = svc.list_competitor_stores()
        assert rows[0]["isActive"] is False
        assert rows[1]["isActive"] is False
        assert rows[2]["isActive"] is False
