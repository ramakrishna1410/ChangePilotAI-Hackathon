using System;

namespace SanofiOrders.Models
{
    public class Order
    {
        public int OrderId { get; set; }
        public string CustomerName { get; set; }
        public decimal TotalAmount { get; set; }
        public OrderStatus Status { get; set; }
        public DateTime CreatedDate { get; set; }
        public int? ApprovedByUserId { get; set; }
        public DateTime? ApprovedDate { get; set; }
    }

    public enum OrderStatus
    {
        Pending = 0,
        AwaitingApproval = 1,
        Approved = 2,
        Rejected = 3,
        Cancelled = 4
    }
}
