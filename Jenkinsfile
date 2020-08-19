pipeline {
	agent any
	
	// In additional to manual runs, trigger somewhere at midnight to
	// give us the max time in a day to get things right without
	// disrupting people.
	
	//triggers {
		// Nightly, between 8pm-12:59pm PDT.
	//	cron('H H(20-23) 1-31 * *')
	//}

	environment {
		
		///
		/// Automatic run variables.
		// Acquire dates and day to beginning of run.
		
		START_DATE = sh (
			script: 'date +%Y-%m-%d',
			returnStdout: true
		).trim()

		START_DAY = sh (
			script: 'date +%A',
			returnStdout: true
		).trim()

		///
		/// Internal run variables.
		///

		// What is the file "namespace" of the ontology--used for
		// finding artifacts.
		ONTOLOGY_FILE_HINT = 'upheno'
		// Ontology repo information.
		TARGET_ONTOLOGY_BRANCH = 'dev-jenkins'
		TARGET_ONTOLOGY_URL = 'https://github.com/obophenotype/upheno-dev.git'
		// The people to call when things go bad or go well. It is a
		// comma-space "separated" string.
		TARGET_ADMIN_EMAILS = 'nicolas.matentzoglu@gmail.com'
		TARGET_SUCCESS_EMAILS = 'nicolas.matentzoglu@gmail.com'
		// This variable should typically be 'TRUE', which will cause
		// some additional basic checks to be made. There are some
		// very exotic cases where these check may need to be skipped
		// for a run, in that case this variable is set to 'FALSE'.
		WE_ARE_BEING_SAFE_P = 'TRUE'
		// Control make to get through our loads faster if
		// possible.
		MAKECMD = 'make'
		// Control the ROBOT environment.
		ROBOT_JAVA_ARGS = '-Xmx150G'
	}
	options{
		//timestamps()
		buildDiscarder(logRotator(numToKeepStr: '14'))
	}
	stages {
	// Very first: check branch sanity and pause for a minute to
	// give a chance to cancel; clean the workspace before use.
		
		stage('Ready and clean') {
			steps {
			// Give us a minute to cancel if we want.
			//sleep time: 1, unit: 'MINUTES'
			cleanWs deleteDirs: true, disableDeferredWipeout: true
			}
		}
		
		stage('Initialize') {
			steps {
				// Upgrading docker image
				sh 'docker pull obolibrary/odkfull:latest'
				// Start preparing environment.
				sh 'env > env.txt'
				sh 'echo $BRANCH_NAME > branch.txt'
				sh 'echo "$BRANCH_NAME"'
				sh 'cat env.txt'
				sh 'cat branch.txt'
				sh 'pwd'
				//sh 'ls -l /var/lib/jenkins/workspace/upheno2-pipeline@2'
				// sh 'chown -R jenkins:jenkins /var/lib/jenkins/workspace/upheno2-pipeline@2/src/curation'
				//sh 'ls -l /var/lib/jenkins/workspace/upheno2-pipeline@2/src/curation'
				sh 'echo $START_DAY > dow.txt'
				sh 'echo "$START_DAY"'
				archiveArtifacts artifacts: "env.txt"
			}
		}
		
		stage('Produce ontology') {
			agent {
				docker {
					image 'obolibrary/odkfull:latest'
					// Reset Jenkins Docker agent default to original
					// root.
					//args '-u root:root -v /foo:/work -e ROBOT_JAVA_ARGS=-Xmx120G'
					args '-u root:root'
					alwaysPull true
				}
			}
			steps {
				// Create a relative working directory and setup our
				// data environment.
				sh 'env > env.txt'
				sh 'cat env.txt'
				sh 'pwd'
				sh 'ls -AlF'
				sh 'ls -AlF /'
				dir('.') {
					git branch: TARGET_ONTOLOGY_BRANCH,
						url: TARGET_ONTOLOGY_URL

					// Default namespace.
					// sh 'OBO=http://purl.obolibrary.org/obo'

					dir('./src/scripts') {
						retry(1){
							sh 'pwd'
							sh 'ls'
							sh 'ls ../curation'
							sh 'ls -l ../curation/pattern-matches'
					// 	//sh 'ls ../curation/tmp'
					// 	//sh 'ls /work'
							sh 'env > env.txt'
							sh 'cat env.txt'
							sh 'sh upheno_pipeline_jenkins.sh'
						}
					}
				dir('./src/ontology') {
					retry(1){
						sh 'ls ../curation/upheno-release'
						sh 'ls ../curation/upheno-release/all'
						//sh 'make sim -B'
					}
				}

					// Move the products to somewhere "safe".
					archiveArtifacts artifacts: "src/curation/tmp/*",
					onlyIfSuccessful: false
					archiveArtifacts artifacts: "src/curation/upheno-release/all/*",
					onlyIfSuccessful: true
					archiveArtifacts artifacts: "src/curation/upheno-release/mp-hp/*",
					onlyIfSuccessful: true
					archiveArtifacts artifacts: "src/curation/upheno-release/mp-hp-dpo/*",
					onlyIfSuccessful: true

					// Now that the files are safely away onto skyhook for
					// debugging, test for the core dump.
					script {
						if( WE_ARE_BEING_SAFE_P == 'TRUE' ){
							def found_core_dump_p = fileExists 'target/core_dump.owl'
							if( found_core_dump_p ){
								error 'ROBOT core dump detected--bailing out.'
							}
						}
					}
				}
			}
		}
		
		// stage('Archive') {
		//     when { anyOf { branch 'release'; branch 'snapshot'; branch 'master' } }
		//     steps {
		// 	// Stanza to push to real file server.
		//     }
		// }
	}
	
	post {
		// Let's let our people know if things go well.
		success {
			script {
			echo "There has been a successful run of the ${env.BRANCH_NAME} pipeline."
			}
		}
		
		// Let's let our internal people know if things change.
		changed {
			echo "There has been a change in the ${env.BRANCH_NAME} pipeline."
		}
	// Let's let our internal people know if things go badly.
		failure {
			echo "There has been a failure in the ${env.BRANCH_NAME} pipeline."
			//mail bcc: '', body: "There has been a pipeline failure in ${env.BRANCH_NAME}. Please see: ${env.JOB_DISPLAY_URL}", cc: '', from: '', replyTo: '', subject: "Pipeline FAIL for ${env.ONTOLOGY_FILE_HINT} on ${env.BRANCH_NAME}", to: "${TARGET_ADMIN_EMAILS}"
		}
	}
}
