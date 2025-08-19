from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, role, full_name=None, department_id=None, email=None, is_active=True, last_login_at=None): # Added last_login_at
        self.id = id
        self.username = username
        self.role = role
        self.full_name = full_name
        self.department_id = department_id
        self.email = email
        self.last_login_at = last_login_at # Store last login time
        self._is_active_status = bool(is_active) # Store the actual active status from DB in a separate attribute

    # Flask-Login requires these properties/methods
    @property
    def is_authenticated(self):
        return True # Assuming if the object exists, the user is authenticated

    @property
    def is_active(self):
        # This overrides the is_active property from UserMixin and returns our stored status
        return self._is_active_status
    # is_anonymous is False by default for authenticated users
    # get_id is handled by UserMixin if self.id is present

class Department:
    def __init__(self, id, name, description=None, created_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at

class Item:
    def __init__(self, id, name, sku=None, description=None, category_id=None, 
                 unit_of_measure=None, reorder_threshold=0.00, 
                 preferred_supplier_id=None, image_path=None, notes=None, 
                 is_active=True, created_at=None, updated_at=None, category_name=None): # Added category_name
        self.id = id
        self.name = name
        self.sku = sku
        self.description = description
        self.category_id = category_id
        self.unit_of_measure = unit_of_measure
        self.reorder_threshold = reorder_threshold
        self.preferred_supplier_id = preferred_supplier_id
        self.image_path = image_path
        self.notes = notes
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
        self.category_name = category_name # To store joined category name

class Location:
    def __init__(self, id, name, description=None, created_at=None, updated_at=None):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at

class Requisition:
    def __init__(self, id, requester_id, department_id=None, status='Pending', 
                 request_date=None, required_by_date=None, approved_by_id=None, 
                 approval_date=None, rejection_reason=None, notes=None, 
                 created_at=None, updated_at=None, requester_name=None, department_name=None, approver_name=None):
        self.id = id
        self.requester_id = requester_id
        self.department_id = department_id
        self.status = status
        self.request_date = request_date
        self.required_by_date = required_by_date
        self.approved_by_id = approved_by_id
        self.approval_date = approval_date
        self.rejection_reason = rejection_reason
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at
        self.requester_name = requester_name # For display
        self.department_name = department_name # For display
        self.approver_name = approver_name # For display

class RequisitionItem:
    def __init__(self, id, requisition_id, item_id, quantity_requested, 
                 quantity_approved=0.00, quantity_issued=0.00, notes=None, item_name=None, item_sku=None, item_unit=None):
        self.id = id
        self.requisition_id = requisition_id
        self.item_id = item_id
        self.quantity_requested = quantity_requested
        self.quantity_approved = quantity_approved
        self.quantity_issued = quantity_issued
        self.notes = notes
        self.item_name = item_name # For display
        self.item_sku = item_sku # For display
        self.item_unit = item_unit # For display

class TrackedAsset:
    def __init__(self, id, item_id, serial_number, status='Available', 
                 assigned_to_user_id=None, office_details=None, 
                 allocation_date=None, purchase_date=None, warranty_expiry_date=None, 
                 notes=None, created_at=None, updated_at=None, 
                 item_name=None, assigned_user_name=None): # Added for display
        self.id = id
        self.item_id = item_id
        self.serial_number = serial_number
        self.status = status # e.g., 'Available', 'Allocated', 'In Repair', 'Disposed'
        self.assigned_to_user_id = assigned_to_user_id
        self.office_details = office_details # E.g., "Office 101, Admin Block"
        self.allocation_date = allocation_date # Date of current allocation or status change
        self.purchase_date = purchase_date
        self.warranty_expiry_date = warranty_expiry_date
        self.notes = notes
        self.item_name = item_name # Joined from items table for display
        self.assigned_user_name = assigned_user_name # Joined from users table for display

class StockTransfer:
    def __init__(self, id, origin_location_id, destination_location_id, initiated_by_user_id, status, transfer_date, 
                 notes=None, driver_details=None, waybill_number=None, completed_by_user_id=None, completion_date=None, 
                 created_at=None, updated_at=None, origin_location_name=None, destination_location_name=None, initiator_name=None):
        self.id = id
        self.origin_location_id = origin_location_id
        self.destination_location_id = destination_location_id
        self.initiated_by_user_id = initiated_by_user_id
        self.status = status
        self.transfer_date = transfer_date
        self.notes = notes
        self.driver_details = driver_details
        self.waybill_number = waybill_number
        self.completed_by_user_id = completed_by_user_id
        self.completion_date = completion_date
        self.created_at = created_at
        self.updated_at = updated_at
        self.origin_location_name = origin_location_name # For display
        self.destination_location_name = destination_location_name # For display
        self.initiator_name = initiator_name # For display

class StockTransferItem:
    def __init__(self, id, transfer_id, item_id, quantity_sent, batch_number=None, expiry_date=None, 
                 quantity_received=None, notes=None, item_name=None, item_sku=None, item_unit=None):
        self.id = id
        self.transfer_id = transfer_id
        self.item_id = item_id
        self.quantity_sent = quantity_sent
        self.batch_number = batch_number
        self.expiry_date = expiry_date
        self.quantity_received = quantity_received
        self.notes = notes
        self.item_name = item_name # For display
        self.item_sku = item_sku # For display
        self.item_unit = item_unit # For display

class Supplier:
    def __init__(self, id, name, contact_person=None, phone=None, email=None, address=None, 
                 payment_terms=None, rating=0.00, is_blacklisted=False, notes=None, 
                 created_at=None, updated_at=None):
        self.id = id
        self.name = name
        self.contact_person = contact_person
        self.phone = phone
        self.email = email
        self.address = address
        self.payment_terms = payment_terms
        self.rating = rating
        self.is_blacklisted = is_blacklisted
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at

class PurchaseOrder:
    def __init__(self, id, supplier_id, order_date, status='Draft', expected_delivery_date=None, 
                 total_amount=0.00, notes=None, created_at=None, updated_at=None, supplier_name=None):
        self.id = id
        self.supplier_id = supplier_id
        self.order_date = order_date
        self.status = status
        self.expected_delivery_date = expected_delivery_date
        self.total_amount = total_amount
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at
        self.supplier_name = supplier_name # For display

class PurchaseOrderItem:
    def __init__(self, id, purchase_order_id, item_id, quantity, unit_price=0.00, 
                 total_price=0.00, item_name=None, item_sku=None, item_unit=None):
        self.id = id
        self.purchase_order_id = purchase_order_id
        self.item_id = item_id
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = total_price
        self.item_name = item_name # For display
        self.item_sku = item_sku # For display
        self.item_unit = item_unit # For display

class GoodsReceivedNote:
    def __init__(self, id, purchase_order_id, received_date, received_by_user_id, 
                 delivery_note_number=None, notes=None, created_at=None, updated_at=None, 
                 purchase_order_number=None, received_by_user_name=None):
        self.id = id
        self.purchase_order_id = purchase_order_id
        self.received_date = received_date
        self.received_by_user_id = received_by_user_id
        self.delivery_note_number = delivery_note_number
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at
        self.purchase_order_number = purchase_order_number # For display
        self.received_by_user_name = received_by_user_name # For display

class GoodsReceivedNoteItem:
    def __init__(self, id, grn_id, item_id, quantity_received, batch_number=None, 
                 expiry_date=None, unit_price=0.00, notes=None, item_name=None, item_sku=None, item_unit=None):
        self.id = id
        self.grn_id = grn_id
        self.item_id = item_id
        self.quantity_received = quantity_received
        self.batch_number = batch_number
        self.expiry_date = expiry_date
        self.unit_price = unit_price
        self.notes = notes
        self.item_name = item_name # For display
        self.item_sku = item_sku # For display
        self.item_unit = item_unit # For display

class Invoice:
    def __init__(self, id, invoice_number, supplier_id, invoice_date, amount, currency='USD', 
                 due_date=None, status='Pending', file_path=None, related_po_id=None, 
                 related_grn_id=None, notes=None, uploaded_by_user_id=None, 
                 created_at=None, updated_at=None, supplier_name=None, uploaded_by_user_name=None):
        self.id = id
        self.invoice_number = invoice_number
        self.supplier_id = supplier_id
        self.invoice_date = invoice_date
        self.amount = amount
        self.currency = currency
        self.due_date = due_date
        self.status = status
        self.file_path = file_path
        self.related_po_id = related_po_id
        self.related_grn_id = related_grn_id
        self.notes = notes
        self.uploaded_by_user_id = uploaded_by_user_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.supplier_name = supplier_name # For display
        self.uploaded_by_user_name = uploaded_by_user_name # For display
