--
-- Generated by VHDL export
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_signed.all;
entity buf_1 is
  port(
      i    : IN std_logic;
      q    : OUT std_logic
  );
end buf_1;



architecture behavioural of buf_1 is

component buf_x2
  port (
  i	: IN STD_LOGIC;
  q	: OUT STD_LOGIC
);
end component;


begin
  buf_x2_i0 : buf_x2
  port map(
       i => i,
       q => q
  );
end behavioural ;
