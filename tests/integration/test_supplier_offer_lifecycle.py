
"""Opt-in MySQL integration tests for the supplier offer lifecycle."""

import os
import uuid
from decimal import Decimal

import pytest

from app.services.supplier_offer_service import SupplierOfferService
from tests.integration.test_database import (
    DatabaseAdapter,
    connect_test_database,
)


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_MYSQL_INTEGRATION_TESTS") != "1",
    reason="MySQL integration tests require explicit opt-in.",
)


@pytest.fixture
def offer_environment():
    """Create isolated fixture records and clean up only those records."""
    connection = connect_test_database()
    db = DatabaseAdapter(connection)
    service = SupplierOfferService(db)

    cursor = None
    created = {
        "category_id": None,
        "supplier_id": None,
        "product_id": None,
        "unit_id": None,
        "package_form_id": None,
        "package_specification_id": None,
        "offer_ids": [],
    }

    token = uuid.uuid4().hex[:12]
    try:
        cursor = db.execute(
            """
            INSERT INTO categories (name, description)
            VALUES (%s, %s)
            """,
            (f"it_category_{token}", "Integration-test fixture"),
        )
        created["category_id"] = cursor.lastrowid
        cursor.close()
        cursor = None

        cursor = db.execute(
            """
            INSERT INTO suppliers (name)
            VALUES (%s)
            """,
            (f"it_supplier_{token}",),
        )
        created["supplier_id"] = cursor.lastrowid
        cursor.close()
        cursor = None

        cursor = db.execute(
            """
            INSERT INTO products (
                category_id, supplier_id, sku, name,
                description, cost_price, selling_price,
                quantity, reorder_level
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                created["category_id"],
                created["supplier_id"],
                f"IT_{token}",
                f"Integration Test Product {token}",
                "Integration-test fixture",
                Decimal("1.00"),
                Decimal("2.00"),
                0,
                0,
            ),
        )
        created["product_id"] = cursor.lastrowid
        cursor.close()
        cursor = None

        cursor = db.execute(
            """
            INSERT INTO units (name, code, unit_type)
            VALUES (%s, %s, %s)
            """,
            (f"IT Unit {token}", f"IT_{token}", "COUNT"),
        )
        created["unit_id"] = cursor.lastrowid
        cursor.close()
        cursor = None

        cursor = db.execute(
            """
            INSERT INTO package_forms (name)
            VALUES (%s)
            """,
            (f"IT Package Form {token}",),
        )
        created["package_form_id"] = cursor.lastrowid
        cursor.close()
        cursor = None

        cursor = db.execute(
            """
            INSERT INTO package_specifications (package_form_id, name)
            VALUES (%s, %s)
            """,
            (
                created["package_form_id"],
                f"IT Package Specification {token}",
            ),
        )
        created["package_specification_id"] = cursor.lastrowid
        cursor.close()
        cursor = None

        db.commit()

        yield {
            "service": service,
            "db": db,
            "created": created,
        }

    finally:
        if cursor is not None:
            cursor.close()

        # Every DELETE is restricted to an ID created by this fixture.
        try:
            cleanup = connection.cursor()
            try:
                offer_ids = created["offer_ids"]
                # Discover offers attached to this fixture's exact IDs.
                # This also catches offers created before their IDs were recorded.
                if (
                    created["supplier_id"] is not None
                    and created["product_id"] is not None
                    and created["package_specification_id"] is not None
                ):
                    cleanup.execute(
                        """
                        SELECT id
                        FROM supplier_offers
                        WHERE supplier_id = %s
                          AND product_id = %s
                          AND package_specification_id = %s
                        """,
                        (
                            created["supplier_id"],
                            created["product_id"],
                            created["package_specification_id"],
                        ),
                    )
                    discovered_offer_ids = [
                        row[0] for row in cleanup.fetchall()
                    ]
                else:
                    discovered_offer_ids = []

                offer_ids = sorted(
                    set(created["offer_ids"]) | set(discovered_offer_ids)
                )

                if offer_ids:
                    placeholders = ", ".join(
                        ["%s"] * len(offer_ids)
                    )
                    cleanup.execute(
                        "DELETE FROM supplier_offer_reviews "
                        f"WHERE supplier_offer_id IN ({placeholders})",
                        tuple(offer_ids),
                    )
                    cleanup.execute(
                        "DELETE FROM supplier_offers "
                        f"WHERE id IN ({placeholders})",
                        tuple(offer_ids),
                    )

                if created["package_specification_id"] is not None:
                    cleanup.execute(
                        "DELETE FROM package_specifications WHERE id = %s",
                        (created["package_specification_id"],),
                    )

                if created["product_id"] is not None:
                    cleanup.execute(
                        "DELETE FROM legacy_product_mapping WHERE product_id = %s",
                        (created["product_id"],),
                    )
                    cleanup.execute(
                        "DELETE FROM products WHERE id = %s",
                        (created["product_id"],),
                    )

                if created["supplier_id"] is not None:
                    cleanup.execute(
                        "DELETE FROM suppliers WHERE id = %s",
                        (created["supplier_id"],),
                    )

                if created["package_form_id"] is not None:
                    cleanup.execute(
                        "DELETE FROM package_forms WHERE id = %s",
                        (created["package_form_id"],),
                    )

                if created["unit_id"] is not None:
                    cleanup.execute(
                        "DELETE FROM units WHERE id = %s",
                        (created["unit_id"],),
                    )

                if created["category_id"] is not None:
                    cleanup.execute(
                        "DELETE FROM categories WHERE id = %s",
                        (created["category_id"],),
                    )

                connection.commit()
            finally:
                cleanup.close()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


def test_supplier_offer_create_update_and_activation_lifecycle(
    offer_environment,
):
    service = offer_environment["service"]
    created = offer_environment["created"]

    supplier_id = created["supplier_id"]
    product_id = created["product_id"]
    package_id = created["package_specification_id"]

    offer_id = service.create_offer(
        supplier_id=supplier_id,
        product_id=product_id,
        package_specification_id=package_id,
        minimum_order_quantity=Decimal("2.0000"),
        purchase_price=Decimal("19.95"),
    )
    created["offer_ids"].append(offer_id)

    offer = service.get_offer(offer_id)
    assert offer is not None
    assert offer[0] == offer_id
    assert offer[1:4] == (supplier_id, product_id, package_id)
    assert Decimal(str(offer[4])) == Decimal("2.0000")
    assert Decimal(str(offer[5])) == Decimal("19.95")
    assert offer[6] in (True, 1)

    assert any(
        row[0] == offer_id
        for row in service.get_offers_by_supplier(supplier_id)
    )
    assert any(
        row[0] == offer_id
        for row in service.get_offers_by_product(product_id)
    )

    with pytest.raises(ValueError, match="already exists"):
        service.create_offer(
            supplier_id=supplier_id,
            product_id=product_id,
            package_specification_id=package_id,
            minimum_order_quantity=Decimal("2.0000"),
            purchase_price=Decimal("19.95"),
        )

    service.update_offer(
        offer_id=offer_id,
        supplier_id=supplier_id,
        product_id=product_id,
        package_specification_id=package_id,
        minimum_order_quantity=Decimal("3.0000"),
        purchase_price=Decimal("21.50"),
        is_active=True,
    )

    updated = service.get_offer(offer_id)
    assert updated is not None
    assert Decimal(str(updated[4])) == Decimal("3.0000")
    assert Decimal(str(updated[5])) == Decimal("21.50")

    service.deactivate_offer(offer_id)

    inactive = service.get_offer(offer_id)
    assert inactive is not None
    assert inactive[6] in (False, 0)
    assert offer_id not in {
        row[0] for row in service.get_all_offers(active_only=True)
    }
    assert offer_id in {
        row[0] for row in service.get_all_offers(active_only=False)
    }

    service.activate_offer(offer_id)

    active = service.get_offer(offer_id)
    assert active is not None
    assert active[6] in (True, 1)
    assert offer_id in {
        row[0] for row in service.get_all_offers(active_only=True)
    }


def test_missing_supplier_offer_behavior(offer_environment):
    service = offer_environment["service"]

    assert service.get_offer(2_000_000_000) is None

    with pytest.raises(ValueError, match="does not exist"):
        service.deactivate_offer(2_000_000_000)

    with pytest.raises(ValueError, match="does not exist"):
        service.update_offer(
            offer_id=2_000_000_000,
            supplier_id=offer_environment["created"]["supplier_id"],
            product_id=offer_environment["created"]["product_id"],
            package_specification_id=offer_environment["created"][
                "package_specification_id"
            ],
            minimum_order_quantity=Decimal("1.0000"),
            purchase_price=Decimal("1.00"),
        )


def test_supplier_offer_review_persistence(offer_environment):
    """Verify review persistence, duplicate protection, and SQL text handling."""
    import os

    from database.supplier_offer_approval import (
        SupplierOfferEvidence,
        SupplierOfferReview,
    )
    from database.supplier_offer_review_service import save_review

    service = offer_environment["service"]
    db = offer_environment["db"]
    created = offer_environment["created"]
    database = os.environ["INVENTORY_TEST_DATABASE"]

    offer_id = service.create_offer(
        supplier_id=created["supplier_id"],
        product_id=created["product_id"],
        package_specification_id=created["package_specification_id"],
        minimum_order_quantity=Decimal("1.0000"),
        purchase_price=Decimal("10.00"),
    )
    created["offer_ids"].append(offer_id)

    review = SupplierOfferReview(
        evidence=SupplierOfferEvidence(
            package_evidence="Package: supplier's sample \\ carton",
            price_evidence="Price: 10 - vendor's quote",
            moq_evidence="MOQ: 1 unit",
        ),
        decision="APPROVED",
        reviewer="O'Brien",
        review_notes="Verified: vendor's file \\ checked - verified",
    )

    save_review(database, offer_id, review)

    def read_review():
        cursor = db.execute(
            """
            SELECT package_evidence, price_evidence, moq_evidence,
                   review_status, reviewer, review_notes
            FROM supplier_offer_reviews
            WHERE supplier_offer_id = %s
            """,
            (offer_id,),
        )
        try:
            return cursor.fetchone()
        finally:
            cursor.close()

    original = read_review()
    assert original is not None
    assert original[0] == review.evidence.package_evidence
    assert original[1] == review.evidence.price_evidence
    assert original[2] == review.evidence.moq_evidence
    assert original[3] == "APPROVED"
    assert original[4] == review.reviewer
    assert original[5] == review.review_notes

    with pytest.raises(ValueError, match="already exists"):
        save_review(database, offer_id, review)

    assert read_review() == original

    with pytest.raises(ValueError, match="does not exist"):
        save_review(database, 2_000_000_000, review)
