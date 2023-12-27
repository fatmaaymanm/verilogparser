`timescale 1ns/1ps

`define true 1'b1
`define false 1'b0

module ATM (
    input clk,
	input rst,
    input [11:0] Account_Number, 
    input [11:0] PIN, 
    input [11:0] Destination_Account,
	input [11:0] WithDraw_Amount,
    input [11:0] Transfer_Amount,
	input [11:0] Deposit_Amount,
	input [2:0] Operation,
    input LC,
	output reg [11:0] FinalBalance,
	output reg [11:0] Final_DstBalance);

parameter S0 = 4'b0000; // WAITING
parameter S1 = 4'b0001; // LANGUAGE CHOICE
parameter S2 = 4'b0010; // REQUEST PIN
parameter S3 = 4'b0011; // AUTHORIZATION
parameter S4 = 4'b0100; // MAIN MENU
parameter S5 = 4'b0101; // DEPOSIT
parameter S6 = 4'b0110; // WITHDRAW
parameter S7 = 4'b0111; // BALANCE SERVICE
parameter S8 = 4'b1000; // TRANSFER
parameter S9 = 4'b1001; // EXIT
parameter S10 = 4'b1010; // CHANGE BALANCE
parameter S11 = 4'b1011; // RECEIPT
parameter S12 = 4'b1100; // CHECK BALANCE
parameter S13 = 4'b1101; // MONEY OUT
parameter S14 = 4'b1110; // SUCCESS
parameter REG_WIDTH = 12;
parameter COL_DEPTH = 4;




reg [3:0] current_state, next_state;
reg [2:0] op;
reg	VP, BC, EA, F, IC, W, T; //ValidPass, BalanceCheck, EnteredAmount, FoundAccount, InsertedCard, Withdraw, Transfer
reg [REG_WIDTH - 1:0] balance, dst_balance; 
reg [REG_WIDTH - 1:0] database [0 : COL_DEPTH - 1] [0:2];
reg [1:0] index1, index2;
//integer i, j;
reg [2:0] i, j;



always @(posedge clk or posedge rst)
	begin
		if (rst)
			begin
				current_state <= S9;
			end
		else	current_state <= next_state;
	end

always @(*) begin
    case (current_state)
        S0: begin

        $readmemh("atm_database.txt", database);

        for (i = 0 ; i < COL_DEPTH ; i = i + 1) begin
        if (Account_Number == database[i][0]) begin
            IC = 1;
            index1 = i;
            i = COL_DEPTH;
        end 
        else begin
            IC = 0;
        end
        end
            BC = 0;
            next_state = S1;
        end

        S1: begin
        if (IC) 
            next_state = S2;
        else
            next_state = S0;
        end

        S2: begin
        if (LC) begin
            if (PIN == database[index1][2]) begin
                VP = 1;
            end
            else begin
                VP = 0;
            end
            next_state = S3;
        end
        else
            next_state = S0;
        end

        S3: begin
        if (VP)
            next_state = S4;
        else 
            next_state = S0;
        end

        S4: begin
        op = Operation;
        case (op)
            3'b000:
            next_state = S5;
            3'b001:
            next_state = S6;
            3'b010:
            next_state = S7;
            3'b011:
            next_state = S8;
            3'b100:
            next_state = S9; 
            default: next_state = S4;
        endcase
        end

        S5: begin
        if (Deposit_Amount > 0) begin
            EA = 1;
            next_state = S10;
        end
        else begin
            EA = 0;
            next_state = S4;
        end
        end

        S6: begin
        if (WithDraw_Amount > 0) begin 
            W = 1;
            next_state = S12;
            end
        else begin
            W = 0;
            next_state = S4;
            end
        end

        S7: begin
        balance = database[index1][1];
        next_state = S11;
        end

        S8: begin
        if (Transfer_Amount > 0) begin
            for (j = 0 ; j < COL_DEPTH ; j = j + 1) begin
                if (Destination_Account == database[j][0]) begin
                    F = 1;
                    index2 = j;
                    j = COL_DEPTH;
                end
                else
                    F = 0;
            end
            if (F) begin
                T = 1;
                next_state = S12;
            end 
            else
                next_state = S4;
        end
        else begin
            T = 0;
            next_state = S4;
        end
        end


        S9: begin
            op = 0;
            VP = 0;
            BC = 0;
            EA = 0;
            F = 0;
            balance = 0;
            dst_balance = 0;
            index1 = 0;
            index2 = 0;
            next_state = S0;
        end

        S10: begin
        if (EA) 
            begin
            balance = database[index1][1] + Deposit_Amount;
            database[index1][1] = balance;
            EA = 0;
            next_state = S11;
            end     
        else if (W && BC) begin
            balance = database[index1][1] - WithDraw_Amount;
            database[index1][1] = balance;
            BC = 0;
            W = 0;
            next_state = S13;
            end
        else if (T && BC) begin
            balance = database[index1][1] - Transfer_Amount;
            database[index1][1] = balance;
            dst_balance = database[index2][1] + Transfer_Amount;
            database[index2][1] = dst_balance;
            BC = 0;
            T = 0;
            next_state = S14;
            end
        else
            next_state = S4;
        end

        S11: begin
        $display("Transaction has been successful! Current Balance is %d", balance);
        next_state = S4;
        end
        
        S12: begin
        balance = database[index1][1];
        if (W) begin
            if(WithDraw_Amount > balance) begin
                BC = 0;
                next_state = S4;
            end
            else begin
                BC = 1;
                next_state = S10;
            end
        end

        else if (T) begin
            if(Transfer_Amount > balance) begin
                BC = 0;
                next_state = S4;
            end
            else begin
                BC = 1;
                next_state = S10;
            end
        end
        end

        S13: begin
            $display("Withdraw has been successful! Current Balance is %d", balance);
            next_state = S4;
        end       
        

        S14: begin
            $display("Transfer has been successful! Current Balance is %d", balance);
            next_state = S4;
        end
        
        
        default: next_state = S0;
    endcase
end

always @(*) begin
    case (current_state)
        S9: begin 
            FinalBalance <= balance;
            Final_DstBalance <= dst_balance;
        end
        S11: FinalBalance <= balance;  
        S13: FinalBalance <= balance; 
        S14: begin 
            FinalBalance <= balance;
            Final_DstBalance <= dst_balance;
        end  
    endcase
end

    
endmodule 