import React, { useEffect } from 'react'
import { connect, Provider } from 'react-redux'
import { BrowserRouter as Router, Link, Route, Switch } from 'react-router-dom'
import { setAuth, setUser } from '../actions'
import Home from "../pages/Home";
import SignUp from "../pages/SignUp";
import SignIn from "../pages/SignIn";
import Profile from "../pages/Profile";
import fetch from "../components/functions/fetchWithTimeOut";
import { csrf_token } from '../components/vars'

function GeneralPage({setAuth, setUser}) {
    useEffect(() => {
        fetch('check_auth/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrf_token
            },
        })
            .then(response => response.json())
            .then(response => {
                if (!response.error) {
                    setUser(response.user)
                    setAuth(true)
                } else {

                }
            })
    }, [])


    return (
        <Router>
            <Switch>
                <Route exact path='/' component={Home} />
                <Route exact path='/signin' component={SignIn} />
                <Route exact path='/signup' component={SignUp} />
                <Route exact path='/profile' component={Profile} />
            </Switch>
        </Router>
    )
}

const mapStateToProps = store => {
    return {
       //
    }
}

const mapDispatchToProps = dispatch => {
    return {
        setAuth: auth => dispatch(setAuth(auth)),
        setUser: user => dispatch(setUser(user))
    }
}

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(GeneralPage)
