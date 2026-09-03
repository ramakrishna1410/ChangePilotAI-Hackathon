using System.Data;
using System.Threading.Tasks;
using SanofiOrders.Models;

namespace SanofiOrders.Repositories
{
    public interface IOrderRepository
    {
        Task<Order> GetByIdAsync(int orderId);
        Task UpdateAsync(Order order);
        Task LogApprovalAsync(int orderId, int approverUserId, string action);
    }

    // Thin ADO.NET wrapper around the Sql/ApprovalProcedures.sql stored procedures.
    public class OrderRepository : IOrderRepository
    {
        private readonly IDbConnection _connection;

        public OrderRepository(IDbConnection connection)
        {
            _connection = connection;
        }

        public async Task<Order> GetByIdAsync(int orderId)
        {
            // Calls dbo.sp_GetOrderById
            return await Dapper.SqlMapper.QuerySingleOrDefaultAsync<Order>(
                _connection, "dbo.sp_GetOrderById", new { OrderId = orderId },
                commandType: CommandType.StoredProcedure);
        }

        public async Task UpdateAsync(Order order)
        {
            // Calls dbo.sp_UpdateOrderStatus
            await Dapper.SqlMapper.ExecuteAsync(
                _connection, "dbo.sp_UpdateOrderStatus",
                new { order.OrderId, Status = (int)order.Status, order.ApprovedByUserId, order.ApprovedDate },
                commandType: CommandType.StoredProcedure);
        }

        public async Task LogApprovalAsync(int orderId, int approverUserId, string action)
        {
            // Calls dbo.sp_InsertApprovalAuditLog
            await Dapper.SqlMapper.ExecuteAsync(
                _connection, "dbo.sp_InsertApprovalAuditLog",
                new { OrderId = orderId, ApproverUserId = approverUserId, Action = action },
                commandType: CommandType.StoredProcedure);
        }
    }
}
