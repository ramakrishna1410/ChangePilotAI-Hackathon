using System.Threading.Tasks;
using SanofiOrders.Models;

namespace SanofiOrders.Services
{
    public interface IOrderApprovalService
    {
        // Returns true if the order was auto-approved, false if it now requires manual approval.
        Task<bool> SubmitForApprovalAsync(int orderId);

        Task ApproveOrderAsync(int orderId, int approverUserId);

        Task RejectOrderAsync(int orderId, int approverUserId, string reason);
    }
}
