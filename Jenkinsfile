pipeline {
    agent any

    environment {
        APP_NAME = "flask-app1" 
        DOCKER_IMAGE = "${env.APP_NAME}:${BUILD_NUMBER}"
        ECR_REPO = "public.ecr.aws/o0y6x7h1/sampleapp" // Your public ECR repo
        AWS_REGION = "us-east-1" // Your AWS region
    }

    stages {
        stage('Clone') {
            steps {
                git branch: 'master', url: 'git@github.com:ijaz-miks/flask-app1.git'
            }
        }

        stage('Build and Test') {
            steps {
                script {
                    // Build the Docker image
                    sh "docker build -t $DOCKER_IMAGE ."

                    // Run tests inside the container
                    def testExitCode = sh(script: "docker run $DOCKER_IMAGE python -m unittest test_app.py", returnStatus: true)
                    if (testExitCode != 0) {
                        error "Unit tests failed!"
                    }
                }
            }
        }

        stage('Push to ECR') {
            steps {
                script {
                    // Get the ECR authorization token
                    def ecrToken = sh(returnStdout: true, script: "aws ecr-public get-login-password --region ${AWS_REGION}")

                    // Log in to ECR using the token
                    sh "docker login --username AWS --password ${ecrToken} ${ECR_REPO.substring(0, ECR_REPO.lastIndexOf('/'))}"

                    // Construct the ECR image tag
                    def ecrImageTag = "${ECR_REPO}/${APP_NAME}:${BUILD_NUMBER}"

                    // Tag the image for ECR
                    sh "docker tag ${DOCKER_IMAGE} ${ecrImageTag}"

                    // Push the image to ECR
                    sh "docker push ${ecrImageTag}"
                }
            }
        }
    }
}