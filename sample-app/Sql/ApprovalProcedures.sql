-- Stored procedures backing SanofiOrders.Repositories.OrderRepository.
-- Referenced by: OrderApprovalService (via OrderRepository).

CREATE PROCEDURE dbo.sp_GetOrderById
    @OrderId INT
AS
BEGIN
    SELECT OrderId, CustomerName, TotalAmount, Status, CreatedDate, ApprovedByUserId, ApprovedDate
    FROM dbo.Orders
    WHERE OrderId = @OrderId;
END
GO

CREATE PROCEDURE dbo.sp_UpdateOrderStatus
    @OrderId INT,
    @Status INT,
    @ApprovedByUserId INT = NULL,
    @ApprovedDate DATETIME = NULL
AS
BEGIN
    UPDATE dbo.Orders
    SET Status = @Status,
        ApprovedByUserId = @ApprovedByUserId,
        ApprovedDate = @ApprovedDate
    WHERE OrderId = @OrderId;
END
GO

-- Shared audit table also written to by the Shipments and Returns modules
-- (see docs/architecture.md) — any schema change here is cross-module impact.
CREATE PROCEDURE dbo.sp_InsertApprovalAuditLog
    @OrderId INT,
    @ApproverUserId INT,
    @Action NVARCHAR(200)
AS
BEGIN
    INSERT INTO dbo.ApprovalAuditLog (OrderId, ApproverUserId, Action, ActionDate)
    VALUES (@OrderId, @ApproverUserId, @Action, GETUTCDATE());
END
GO

-- Used by the nightly BatchApprovalRunner job to find orders stuck awaiting approval.
CREATE PROCEDURE dbo.sp_GetPendingApprovals
    @OlderThanHours INT = 24
AS
BEGIN
    SELECT OrderId, CustomerName, TotalAmount, CreatedDate
    FROM dbo.Orders
    WHERE Status = 1 -- AwaitingApproval
      AND CreatedDate <= DATEADD(HOUR, -@OlderThanHours, GETUTCDATE());
END
GO
