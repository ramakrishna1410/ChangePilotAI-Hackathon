using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using SanofiOrders.Services;

namespace SanofiOrders.Controllers
{
    [ApiController]
    [Route("api/orders/{orderId}/approval")]
    public class OrderApprovalController : ControllerBase
    {
        private readonly IOrderApprovalService _approvalService;

        public OrderApprovalController(IOrderApprovalService approvalService)
        {
            _approvalService = approvalService;
        }

        // POST api/orders/5/approval/submit
        [HttpPost("submit")]
        public async Task<IActionResult> Submit(int orderId)
        {
            var autoApproved = await _approvalService.SubmitForApprovalAsync(orderId);
            return Ok(new { orderId, autoApproved });
        }

        // POST api/orders/5/approval/approve
        [HttpPost("approve")]
        public async Task<IActionResult> Approve(int orderId, [FromQuery] int approverUserId)
        {
            await _approvalService.ApproveOrderAsync(orderId, approverUserId);
            return NoContent();
        }

        // POST api/orders/5/approval/reject
        [HttpPost("reject")]
        public async Task<IActionResult> Reject(int orderId, [FromQuery] int approverUserId, [FromBody] string reason)
        {
            await _approvalService.RejectOrderAsync(orderId, approverUserId, reason);
            return NoContent();
        }
    }
}
