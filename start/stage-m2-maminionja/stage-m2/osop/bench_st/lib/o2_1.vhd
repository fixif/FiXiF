--
-- Generated by VHDL export
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_signed.all;
entity o2_1 is
  port(
      i0    : IN std_logic;
      i1    : IN std_logic;
      q    : OUT std_logic
  );
end o2_1;



architecture behavioural of o2_1 is

component hs65_ls_or2x4
  port (
  a	: IN STD_LOGIC;
  b	: IN STD_LOGIC;
  z	: OUT STD_LOGIC
);
end component;


begin
  o2_x2_i0 : hs65_ls_or2x4
  port map(
       a => i1,
       b => i0,
       z => q
  );
end behavioural ;
