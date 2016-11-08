import React, { Component } from 'react'
import moment from 'moment'
import './App.css'

import thread from './dummy/thread'
import posts from './dummy/posts'
const poll = false

class App extends Component {
  render() {
    return (
      <div className="container-fluid">
        <div className="row">
          <div className="col-lg-10 col-lg-offset-1">
            <div style={{paddingTop: "8px"}} />
            <ThreadContainer />
          </div>
        </div>
      </div>
    )
  }
}

class ThreadContainer extends Component {
  render() {
    return (
      <div className="thread-container">
        <Title title={thread.title} type={poll ? 'Sondage' : 'Sujet'}/>
        <PostList posts={posts} />
      </div>
    )
  }
}

const Title = (props) => {
  return (
    <div className="thread-title">
      <div className="row">
        <div className="col-sm-2 hidden-xs left-side">
          <div className="content">Auteur</div>
        </div>
        <div className="col-sm-10">
          <div className="content">{props.type} : {props.title}</div>
        </div>
      </div>
      <hr />
    </div>
  )
}

const PostList = (props) => {

  // TODO: Replace canEdit placeholder
  const renderPost = (post) => (
    <div>
      <div className="row" key={post.id}>
        <PostAuthor {...post.author} />
        <PostMessage {...post} canEdit={false} />
      </div>
      <hr />
    </div>
  )

  return (
    <div className="post-list">
      {posts.map(renderPost)}
    </div>
  )
}

const PostAuthor = (props) => {
  return (
    <div className="col-sm-2 hidden-xs text-center author left-side">
      <div className="frame">
        <p className="username">{props.username}</p>
        {props.quote ? <p className="quote">{props.quote}</p> : null}
        {props.logo ? (
          <p><img src={`./${props.logo}`} alt={`${props.username} logo`}/></p>
        ) : null}
        <p className="footer">
          depuis le {moment(props.date_joined).format('DD/MM/YYYY')}
        </p>
      </div>
    </div>
  )
}

const PostMessage = ({author, content, created, modified, canEdit}) => {

  const formattedDate = (d) => moment(d).format('DD/MM/YYYY à HH:mm:ss') 

  const Header = () => (
    <div className="header">
      <span className="hidden-xs">Posté le {formattedDate(created)}</span>
      <span className="hidden-sm hidden-lg hidden-md">
        <span className="username">
          {author.username}
        </span> | Le {formattedDate(created)}
      </span>
      <span> | </span>
      <a href="">Citer</a>
      <span> | </span>
      {canEdit ? (
        <span>
          <a href="">Modifier</a>
          <span> | </span>
        </span>
      ) : null}
      <a href=""><span className="glyphicon glyphicon-link"></span></a>
    </div>
  )

  return (
    <div className="col-sm-10 message">
      <div className="frame">
        <Header />
        <hr />
        <div className="content">{content}</div>
        <br />
        <p className="footer">— Modifié le {formattedDate(modified)}</p>
      </div>
    </div>
  )
}

export default App