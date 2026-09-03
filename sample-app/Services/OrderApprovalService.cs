using System;
using System.Threading.Tasks;
using SanofiOrders.Models;
using SanofiOrders.Repositories;

namespace SanofiOrders.Services
{
    // Handles the order approval workflow. Called by OrderApprovalController and by the
    // nightly batch job (BatchApprovalRunner) that re-checks orders left in AwaitingApproval.
    public class OrderApprovalService : IOrderApprovalService
    {
        private readonly IOrderRepository _orderRepository;
        private readonly INotificationService _notificationService;

        public OrderApprovalService(IOrderRepository orderRepository, INotificationService notificationService)
        {
            _orderRepository = orderRepository;
            _notificationService = notificationService;
        }

        public async Task<bool> SubmitForApprovalAsync(int orderId)
        {
            var order = await _orderRepository.GetByIdAsync(orderId);
            if (order == null)
                throw new InvalidOperationException($"Order {orderId} not found.");

            // Current business rule: every order requires manual Tech Lead / Finance approval
            // before it moves to Approved, regardless of amount. There is no auto-approval path
            // today. (Candidate location for the "auto-approve below threshold" business rule.)
            order.Status = OrderStatus.AwaitingApproval;
            await _orderRepository.UpdateAsync(order);
            await _notificationService.NotifyApproversAsync(order);

            return false;
        }

        public async Task ApproveOrderAsync(int orderId, int approverUserId)
        {
            var order = await _orderRepository.GetByIdAsync(orderId);
            if (order == null)
                throw new InvalidOperationException($"Order {orderId} not found.");

            order.Status = OrderStatus.Approved;
            order.ApprovedByUserId = approverUserId;
            order.ApprovedDate = DateTime.UtcNow;

            await _orderRepository.UpdateAsync(order);
            await _orderRepository.LogApprovalAsync(orderId, approverUserId, "Approved");
            await _notificationService.NotifyCustomerAsync(order, approved: true);
        }

        public async Task RejectOrderAsync(int orderId, int approverUserId, string reason)
        {
            var order = await _orderRepository.GetByIdAsync(orderId);
            if (order == null)
                throw new InvalidOperationException($"Order {orderId} not found.");

            order.Status = OrderStatus.Rejected;
            await _orderRepository.UpdateAsync(order);
            await _orderRepository.LogApprovalAsync(orderId, approverUserId, $"Rejected: {reason}");
            await _notificationService.NotifyCustomerAsync(order, approved: false);
        }
    }

    // Consumed by OrderApprovalService and by ShipmentNotificationJob (downstream service).
    public interface INotificationService
    {
        Task NotifyApproversAsync(Order order);
        Task NotifyCustomerAsync(Order order, bool approved);
    }
}
