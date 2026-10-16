class CongestionControl:
    def __init__(self, MSS: int):
        self.MSS = MSS
        self.cwnd = 1 * MSS
        self.ssthresh = None
        self.current_state = "slow_start"

    def get_cwnd(self) -> int:
        return self.cwnd
    def get_MSS_in_cwnd(self) -> int:
        return self.cwnd // self.MSS
    
    def event_ack_received(self) -> None:
        if self.current_state == "slow_start":
            self.cwnd += self.MSS
            # si cwnd lo alcanza o supera a ssthresh, pasamos a congestion avoidance
            if self.ssthresh is not None and self.cwnd >= self.ssthresh:
                self.current_state = "congestion_avoidance"

        elif self.current_state == "congestion_avoidance":
            mss_in_cwnd = self.get_MSS_in_cwnd()
            if mss_in_cwnd > 0:
                self.cwnd += self.MSS / mss_in_cwnd
    def event_timeout(self) -> None:
        self.ssthresh = self.cwnd // 2
        #reseteo
        self.cwnd = 1 * self.MSS
        self.current_state = "slow_start"




    def is_state_slow_start(self) -> bool:
        return self.current_state == "slow_start"
    
    
    def is_state_congestion_avoidance(self) -> bool:
        return self.current_state == "congestion_avoidance"
    
    def get_ssthresh(self):
        return self.ssthresh