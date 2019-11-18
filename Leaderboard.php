<!DOCTYPE html>
<?php
	if (empty($_SESSION["Refresh_Time"])) {
		session_start();
	}
	
	if (isset($_POST["Refresh_Time"])) {
		$_SESSION["Refresh_Time"] = $_POST["Refresh_Time"];
	} 
	if (empty($_SESSION["Refresh_Time"])) {
		$_SESSION["Refresh_Time"] = 30;
	}
?>
<html>
<head>
	<meta http-equiv="refresh" content=<?php if(isset($_SESSION["Refresh_Time"])){ echo $_SESSION["Refresh_Time"];} else { echo 30; }?>>
	<title>Leaderboard</title>
	<?php	
		foreach(array_keys($_SESSION) as $keys) {
			if(isset($_GET[$keys])) {
				$_SESSION[str_replace(' ', '_', $keys)] = $_GET[$keys];
			}
			else if ($keys != "Refresh_Time" && strlen($keys)<30) {
				$_SESSION[str_replace(' ', '_', $keys)] = "off";
			}
		}

		require __DIR__ . '/vendor/autoload.php';
		use Ramsey\Uuid\Uuid;
		$ranking = 1;
		$cassandra = "cassandra";
		$ipList = file_get_contents("ips.txt");
		$ipArray = str_getcsv($ipList);
		$ipString = "";
		foreach ($ipArray as $ip) {
			$ipString.= $ip;
			$ipString.=",";
		}
		
		$ipString = substr($ipString, 0, -1);
		
		$cluster = Cassandra::cluster()
				->withContactPoints($ipString)
				->withCredentials($cassandra, $cassandra)
				->build();
		try {
			$session = $cluster->connect("competition");
		} catch (Cassandra\Exception $e) {
			echo get_class($e) . ": " . $e->getMessage() . "\n";
		}
		
		$getGroupsStatement = new Cassandra\SimpleStatement("SELECT group FROM positional GROUP BY flight_id");
		$result = $session->execute($getGroupsStatement);
		
		$i = 0;
		$groupResults = [];
		foreach ($result as $row) {
			$group = str_replace(' ', '_', $row["group"]);
			if (!in_array($row, $groupResults)) {
				$groupResults[$i]["group"] = $group;
				if (empty($_SESSION[str_replace(' ', '_', $group)])) {
					if ($group == "Test_Group") {
						$_SESSION[str_replace(' ', '_', $group)] = "off";
					}
					else {	
						$_SESSION[str_replace(' ', '_', $group)] = "on";
					}
				}
				$i++;
			}
		}
		sort($groupResults);
	?>
		<style>
		.wrap {
			min-height: 100%;
		}
		.container {
			position: relative;
		}
		 .leaderboard {
			width: 100%;
			border-collapse: collapse;
			border-spacing: 0;
			font-size: 14px;
			line-height: 20px;
		}
		.leaderboard>tbody>tr>td {
			text-align: center;
			padding: 13px;
		}
		div {
			display: block;
		}
		thead {
			display: table-header-group;
			vertical-align: middle;
			border-color: inherit;
		}
		.odd {
			background-color: #f7f7f7;
		}
		.even {
			background-color: #fff;
		}
		.recent {
			background-color: #00ff00;
		}
		tr td {
			white-space: nowrap;
		}
		.R1 {
			background-color: gold;
			height: 75px;
		}
		.R2 {
			background-color: silver;
			height: 65px;
		}
		.R3 {
			background-color: #cd7f32;
			height: 55px;
		}
		.button {
			width: 100px;
			text-align: center;
			margin-bottom: 10px;
		}
		.footer {
			position: relative;
			bottom: 0;
		}

		</style>
</head>
<body>
<div class="wrap">
    <div class="container">
		<table class="leaderboard">
			<thead class="odd">
				<th class="Ranking">
					Ranking
				</th>
				<th class="Name">
					Name
				</th>
				<th class="Flight_Time">
					Flight Time
				</th>
				<th class="Group">
					Group
				</th>
				<th class="College/Org">
					College/Org
				</th>
				<th class="Major">
					Major
				</th>
			</thead>
			<tbody>
				<?php
					$getStatement = new Cassandra\SimpleStatement("SELECT flight_id, latest_ts FROM positional GROUP BY flight_id");
					$result = $session->execute($getStatement);
					$flights= [];
					$i = 0;
					foreach($result as $row) {
						$temp = array("flight_id" => $row["flight_id"], "timestamp" => $row["latest_ts"]);
						array_push($flights, $temp);
					}
					
					$ts = array_column($flights, "timestamp");
					array_multisort($ts, SORT_DESC, $flights);
					
					$recent = array_slice($flights, 0, 4, true);
					
					$recentCounts = [];
					foreach($recent as $id) {
						$getStatement = new Cassandra\SimpleStatement("SELECT flight_id, count(*) FROM positional WHERE flight_id = ".$id["flight_id"]);
						$result = $session->execute($getStatement);
						array_push($recentCounts, $result);
					}
					
					$mostRecentTwo = [];
					foreach($recentCounts as $flights) {
						foreach($flights as $sub) {
							$vars = get_object_vars($sub["count"]);
							if(isset($_SESSION[(string)$sub["flight_id"]])) {
								if($vars["value"] == $_SESSION[(string)$sub["flight_id"]] && count($mostRecentTwo)<2) {
									array_push($mostRecentTwo, $sub["flight_id"]);
								}
								else {
									$_SESSION[(string)$sub["flight_id"]] = $vars["value"];
								}
							}
							else {
								$_SESSION[(string)$sub["flight_id"]] = $vars["value"];
							}
						}
					}

					$recentFlights = [];
					$i = 0;
					$leaderboardCode = "";
					
					foreach($mostRecentTwo as $recents) {
						$getAllStatement = new Cassandra\SimpleStatement("SELECT name,flight_id,latest_ts,group,org_college,major FROM positional WHERE flight_id = ".$recents." GROUP BY flight_id");
						$result = $session->execute($getAllStatement);

						foreach($result as $row) {
							$recentFlights[$i]["name"] = $row["name"];
							$recentFlights[$i]["time"] = (($row["latest_ts"]->time()+14400)-(strtotime(Uuid::fromString($row["flight_id"])->getDateTime()->format('r'))));
							$recentFlights[$i]["group"] = $row["group"];
							$recentFlights[$i]["org"] = $row["org_college"];
							$recentFlights[$i]["major"] = $row["major"];
							$i++;
					}
					}

					foreach($recentFlights as $row) {
						$evenOdd = "recent";
						$leaderboardCode .= "<tr class=\"".$evenOdd."\"> 
								<td class=\"Ranking\"> Recent </td>
								<td class=\"Name\">" . $row["name"] . "</td>
								<td class=\"Flight_Time\">".gmdate("i:s", $row["time"])."</td>									
								<td class=\"Group\">" . $row["group"] . "</td>									
								<td class=\"College/Org\">" . $row["org"] . "</td>									
								<td class=\"Major\">" . $row["major"] . "</td>				
							</tr>";
					}


					$getAllStatement = new Cassandra\SimpleStatement("SELECT name,flight_id,latest_ts,group,org_college,major FROM positional GROUP BY flight_id");
					$result = $session->execute($getAllStatement);
					
					$leaderboardResults = [];					
					$i = 0;
					foreach($result as $row) {
						echo $row["name"];
						$leaderboardResults[$i]["name"] = $row["name"];
						$leaderboardResults[$i]["time"] = (($row["latest_ts"]->time()+14400)-(strtotime(Uuid::fromString($row["flight_id"])->getDateTime()->format('r'))));
						$leaderboardResults[$i]["group"] = $row["group"];
						$leaderboardResults[$i]["org"] = $row["org_college"];
						$leaderboardResults[$i]["major"] = $row["major"];
						$i++;
					}

					array_multisort(array_column($leaderboardResults,"time"), SORT_ASC, $leaderboardResults);

					foreach ($leaderboardResults as $row) {
						try {
							if($_SESSION[str_replace(' ', '_', $row["group"])] == "on") {
								if ($ranking % 2 == 0) {
									$evenOdd = "even";
								} else {
									$evenOdd = "odd";
								}
								$leaderboardCode .= "<tr class=\"".$evenOdd." R".$ranking."\">
										<td class=\"Ranking\">" . $ranking++ . "</td>
										<td class=\"Name\">" . $row["name"] . "</td>
										<td class=\"Flight_Time\">".gmdate("i:s", $row["time"])."</td>									
										<td class=\"Group\">" . $row["group"] . "</td>									
										<td class=\"College/Org\">" . $row["org"] . "</td>									
										<td class=\"Major\">" . $row["major"] . "</td>				
									</tr>";
							}
						} catch (Exception $e) {}
					}
					echo $leaderboardCode;
				?>
			</tbody>
		</table>
	</div>
	<div class="footer">
		<form action="" method="post">
			<button class="button" type="submit" name="Refresh_Time" value="1">1 Second</button>
			<button class="button" type="submit" name="Refresh_Time" value="5">5 Seconds</button>
			<button class="button" type="submit" name="Refresh_Time" value="10">10 Seconds</button>
			<button class="button" type="submit" name="Refresh_Time" value="15">15 Seconds</button>
			<button class="button" type="submit" name="Refresh_Time" value="30">30 Seconds</button>
			<button class="button" type="submit" name="Refresh_Time" value="0">Live</button>
		</form>
		<br/>
		<form action="" method="get">
			<?php
				$groupCode = "";
				foreach ($groupResults as $group) {
					if ($_SESSION[str_replace(' ', '_', $group["group"])] == "on") {
						$groupCode .= "<p><input type=\"checkbox\" name=\"" . $group["group"] . "\" onchange=\"this.form.submit()\" checked>" . $group["group"] . "</p>";
					} else {	
						$groupCode .= "<p><input type=\"checkbox\" name=\"" . $group["group"] . "\" onchange=\"this.form.submit()\">" . $group["group"] . "</p>";
					}
				}
				echo $groupCode;
			?>
		</form>
	</div>
</div>
</body>
</html>