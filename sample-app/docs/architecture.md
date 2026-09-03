# SanofiOrders — Order Approval Module (Architecture Notes)

## Purpose
Handles the order approval workflow for the SanofiOrders application: an order
submitted above certain business conditions must be routed through manual
approval before it can ship.

## Components
- `Controllers/OrderApprovalController` — REST endpoints: submit, approve, reject.
- `Services/OrderApprovalService` (implements `IOrderApprovalService`) — business
  logic for the approval workflow. Also invoked by the nightly `BatchApprovalRunner`
  job (not included in this sample) which re-checks orders left in
  `AwaitingApproval` using `dbo.sp_GetPendingApprovals`.
- `Repositories/OrderRepository` — ADO.NET/Dapper access to `dbo.Orders` and
  `dbo.ApprovalAuditLog` via the stored procedures in `Sql/ApprovalProcedures.sql`.
- `Models/Order` — order entity and `OrderStatus` enum.
- `INotificationService` — downstream dependency; also consumed by the
  `ShipmentNotificationJob` service (outside this module) to notify customers
  once shipments go out.

## Current Business Rule
Every order requires manual approval before moving to `Approved` — there is
**no automatic approval path** today, regardless of order amount. All orders
submitted via `SubmitForApprovalAsync` move to `AwaitingApproval` and wait for
a human approver to call `ApproveOrderAsync` or `RejectOrderAsync`.

## Shared / Cross-Module Dependencies
- `dbo.ApprovalAuditLog` is also written to by the Shipments and Returns
  modules — schema changes require coordination with those teams.
- `INotificationService` is shared with `ShipmentNotificationJob`.
- The nightly `BatchApprovalRunner` batch job depends on `OrderApprovalService`
  and `sp_GetPendingApprovals` — changes to the approval state machine affect
  this job too.

## Known Gaps
- No configurable approval threshold currently exists in code or configuration.
- No audit trail for *why* an order required approval (only that it did).
